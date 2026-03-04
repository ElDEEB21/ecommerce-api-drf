import logging

from django.core.exceptions import ValidationError, PermissionDenied
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    PaymentSerializer,
    PaymentStatusSerializer,
    CreatePaymentIntentSerializer,
    PaymentIntentResponseSerializer,
    CancelPaymentSerializer,
    RefundPaymentSerializer,
    SyncPaymentStatusSerializer,
    PaymentStatisticsSerializer,
)
from .. import selectors
from ..services import PaymentService, StripeWebhookService

logger = logging.getLogger(__name__)


class CreatePaymentIntentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreatePaymentIntentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        try:
            result = PaymentService.create_payment_intent(
                order_id=validated_data['order_id'],
                user=request.user,
                currency=validated_data.get('currency'),
                idempotency_key=validated_data.get('idempotency_key'),
            )
            response_serializer = PaymentIntentResponseSerializer(result)
            logger.info(
                f"Payment intent created for order {validated_data['order_id']} "
                f"by user {request.user.id}"
            )
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            logger.warning(f"Payment intent creation failed: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PermissionDenied as e:
            logger.warning(f"Permission denied for payment: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_403_FORBIDDEN
            )


class PaymentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, payment_id):
        payment = selectors.get_payment_by_id(payment_id)
        if not payment:
            return Response(
                {"error": "Payment not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        if payment.order.user != request.user and not request.user.is_staff:
            return Response(
                {"error": "You don't have permission to view this payment."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PaymentSerializer(payment)
        return Response(serializer.data)


class PaymentByOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        payment = selectors.get_payment_by_order(order_id)
        if not payment:
            return Response(
                {"error": "No payment found for this order."},
                status=status.HTTP_404_NOT_FOUND
            )
        if payment.order.user != request.user and not request.user.is_staff:
            return Response(
                {"error": "You don't have permission to view this payment."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PaymentSerializer(payment)
        return Response(serializer.data)


class PaymentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        status_filter = request.query_params.get('status')
        payments = selectors.get_user_payments(
            user=request.user,
            status=status_filter
        )
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)


class PaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, payment_id):
        payment = selectors.get_payment_by_id(payment_id)
        if not payment:
            return Response(
                {"error": "Payment not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        if payment.order.user != request.user and not request.user.is_staff:
            return Response(
                {"error": "Not authorized."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PaymentStatusSerializer(payment)
        return Response(serializer.data)


class CancelPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CancelPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payment = PaymentService.cancel_payment(
                payment_id=serializer.validated_data['payment_id'],
                user=request.user
            )
            logger.info(f"Payment {payment.id} cancelled by user {request.user.id}")
            return Response({
                "message": "Payment cancelled successfully.",
                "payment": PaymentSerializer(payment).data
            })
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PermissionDenied as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_403_FORBIDDEN
            )


class RefundPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RefundPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = PaymentService.refund_payment(
                payment_id=serializer.validated_data['payment_id'],
                user=request.user,
                amount=serializer.validated_data.get('amount'),
                reason=serializer.validated_data.get('reason')
            )
            logger.info(
                f"Payment {result['payment'].id} refunded by user {request.user.id}"
            )
            return Response({
                "message": "Payment refunded successfully.",
                "payment": PaymentSerializer(result['payment']).data
            })
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PermissionDenied as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_403_FORBIDDEN
            )


class SyncPaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SyncPaymentStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payment = PaymentService.sync_payment_status(
                payment_intent_id=serializer.validated_data['payment_intent_id']
            )
            if payment.order.user != request.user and not request.user.is_staff:
                return Response(
                    {"error": "Not authorized."},
                    status=status.HTTP_403_FORBIDDEN
                )
            return Response({
                "message": "Payment status synced.",
                "payment": PaymentSerializer(payment).data
            })
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class PaymentStatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stats = selectors.get_payment_statistics(request.user)
        serializer = PaymentStatisticsSerializer(stats)
        return Response(serializer.data)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        if not sig_header:
            logger.warning("Webhook received without Stripe-Signature header")
            return Response(
                {"error": "Missing Stripe-Signature header."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            event = StripeWebhookService.verify_webhook(payload, sig_header)
            result = StripeWebhookService.handle_event(event)
            logger.info(f"Webhook processed: {event.type} - {result['status']}")
            return Response({
                "status": result['status'],
                "message": result['message']
            })
        except ValidationError as e:
            logger.warning(f"Webhook validation failed: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Webhook processing error: {e}", exc_info=True)
            return Response({
                "status": "error",
                "message": "Internal error processing webhook."
            })


class PublishableKeyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.conf import settings

        return Response({
            "publishable_key": settings.STRIPE_PUBLISHABLE_KEY
        })
