import logging
import uuid
from decimal import Decimal
from typing import Dict, Any

import stripe
from django.conf import settings
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.db.models import F

from .models import Payment
from ..orders.models import Order
from ..orders.services import OrderService
from ..products.models import Product

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentService:

    @staticmethod
    def _convert_to_stripe_amount(amount: Decimal, currency: str = 'usd') -> int:
        zero_decimal_currencies = [
            'bif', 'clp', 'djf', 'gnf', 'jpy', 'kmf', 'krw', 'mga',
            'pyg', 'rwf', 'ugx', 'vnd', 'vuv', 'xaf', 'xof', 'xpf'
        ]

        if currency.lower() in zero_decimal_currencies:
            return int(amount)
        return int(amount * 100)

    @staticmethod
    def _generate_idempotency_key(order_id: int) -> str:
        return f"order_{order_id}_{uuid.uuid4().hex}"

    @staticmethod
    def _cancel_order_and_restore_stock(order_id: int, reason: str = '') -> None:
        order = Order.objects.select_for_update().get(id=order_id)
        if order.status not in [Order.Status.PENDING, Order.Status.PROCESSING]:
            return
        order.status = Order.Status.CANCELLED
        order.save(update_fields=['status', 'updated_at'])
        for item in order.items.select_related('product').all():
            Product.objects.filter(id=item.product_id).update(
                stock_quantity=F('stock_quantity') + item.quantity
            )

        logger.info(f"Order {order.id} cancelled and stock restored{f' ({reason})' if reason else ''}")

    @staticmethod
    @transaction.atomic
    def create_payment_intent(order_id: int, user, currency: str = None, idempotency_key: str = None) -> Dict[str, Any]:
        currency = currency or getattr(settings, 'STRIPE_CURRENCY', 'usd')
        try:
            order = Order.objects.select_for_update().get(id=order_id)
        except Order.DoesNotExist:
            logger.warning(f"Payment attempt for non-existent order: {order_id}")
            raise ValidationError(f"Order with ID {order_id} not found.")

        if order.user != user:
            logger.warning(
                f"Unauthorized payment attempt: User {user.id} tried to pay for order {order_id} "
                f"owned by user {order.user.id}"
            )
            raise PermissionDenied("You don't have permission to pay for this order.")

        if order.status not in [Order.Status.PENDING, Order.Status.PROCESSING]:
            raise ValidationError(
                f"Order is not in a payable status. Current status: {order.status}"
            )

        existing_payment = Payment.objects.filter(order=order).first()
        if existing_payment:
            if existing_payment.is_successful:
                raise ValidationError("This order has already been paid.")

            if existing_payment.status in [Payment.Status.PENDING, Payment.Status.FAILED]:
                try:
                    intent = stripe.PaymentIntent.retrieve(
                        existing_payment.stripe_payment_intent_id
                    )

                    existing_payment.client_secret = intent.client_secret
                    existing_payment.save(update_fields=['client_secret', 'updated_at'])

                    logger.info(f"Returning existing payment intent for order {order_id}")
                    return {
                        'payment': existing_payment,
                        'client_secret': intent.client_secret,
                        'publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
                    }
                except stripe.error.StripeError as e:
                    logger.warning(f"Could not retrieve existing PaymentIntent: {e}")
                    existing_payment.delete()

        if not idempotency_key:
            idempotency_key = PaymentService._generate_idempotency_key(order_id)

        stripe_amount = PaymentService._convert_to_stripe_amount(order.total_amount, currency)

        try:
            intent = stripe.PaymentIntent.create(
                amount=stripe_amount,
                currency=currency.lower(),
                metadata={'order_id': str(order.id), 'user_id': str(user.id), 'user_email': user.email, },
                automatic_payment_methods={'enabled': True, },
                idempotency_key=idempotency_key,
                description=f"Payment for Order #{order.id}",
            )

            logger.info(
                f"Created PaymentIntent {intent.id} for order {order_id}, "
                f"amount: {stripe_amount} {currency}"
            )
            payment = Payment.objects.create(
                order=order,
                stripe_payment_intent_id=intent.id,
                status=Payment.Status.PENDING,
                amount=order.total_amount,
                currency=currency.lower(),
                idempotency_key=idempotency_key,
                client_secret=intent.client_secret,
            )
            return {
                'payment': payment,
                'client_secret': intent.client_secret,
                'publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
            }

        except stripe.error.CardError as e:
            logger.warning(f"Card declined for order {order_id}: {e.user_message}")
            raise ValidationError(f"Card declined: {e.user_message}")
        except stripe.error.RateLimitError as e:
            logger.error(f"Stripe rate limit exceeded: {e}")
            raise ValidationError("Payment service is busy. Please try again.")
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Invalid Stripe request for order {order_id}: {e}")
            raise ValidationError("Invalid payment request. Please contact support.")
        except stripe.error.AuthenticationError as e:
            logger.critical(f"Stripe authentication failed: {e}")
            raise ValidationError("Payment service configuration error.")
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error for order {order_id}: {e}")
            raise ValidationError("Payment processing error. Please try again.")

    @staticmethod
    @transaction.atomic
    def sync_payment_status(payment_intent_id: str) -> Payment:
        try:
            payment = Payment.objects.select_for_update().get(
                stripe_payment_intent_id=payment_intent_id
            )
        except Payment.DoesNotExist:
            raise ValidationError(f"Payment with intent {payment_intent_id} not found.")

        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            status_mapping = {
                'requires_payment_method': Payment.Status.PENDING,
                'requires_confirmation': Payment.Status.PENDING,
                'requires_action': Payment.Status.PROCESSING,
                'processing': Payment.Status.PROCESSING,
                'requires_capture': Payment.Status.PROCESSING,
                'canceled': Payment.Status.CANCELLED,
                'succeeded': Payment.Status.SUCCEEDED,
            }

            new_status = status_mapping.get(intent.status, Payment.Status.PENDING)
            old_status = payment.status
            payment.status = new_status

            if intent.last_payment_error:
                payment.status = Payment.Status.FAILED
                payment.failure_message = intent.last_payment_error.get('message', 'Unknown error')

            payment.save()
            logger.info(
                f"Synced payment {payment.id}: {old_status} -> {payment.status}"
            )
            return payment
        except stripe.error.StripeError as e:
            logger.error(f"Error syncing payment status: {e}")
            raise ValidationError("Could not retrieve payment status from Stripe.")

    @staticmethod
    @transaction.atomic
    def cancel_payment(payment_id: int, user) -> Payment:
        try:
            payment = Payment.objects.select_for_update().get(id=payment_id)
        except Payment.DoesNotExist:
            raise ValidationError("Payment not found.")

        if payment.order.user != user:
            raise PermissionDenied("You don't have permission to cancel this payment.")
        if payment.status not in [Payment.Status.PENDING, Payment.Status.PROCESSING]:
            raise ValidationError(
                f"Cannot cancel payment with status: {payment.status}. "
                f"Only pending or processing payments can be cancelled."
            )

        try:
            stripe.PaymentIntent.cancel(payment.stripe_payment_intent_id)
            payment.status = Payment.Status.CANCELLED
            payment.save(update_fields=['status', 'updated_at'])

            logger.info(f"Cancelled payment {payment_id} for order {payment.order_id}")
            PaymentService._cancel_order_and_restore_stock(
                payment.order_id, reason='payment cancelled'
            )

            return payment
        except stripe.error.StripeError as e:
            logger.error(f"Error cancelling payment {payment_id}: {e}")
            raise ValidationError("Could not cancel payment. Please try again.")

    @staticmethod
    @transaction.atomic
    def refund_payment(payment_id: int, user, amount: Decimal = None, reason: str = None) -> Dict[str, Any]:
        try:
            payment = Payment.objects.select_for_update().get(id=payment_id)
        except Payment.DoesNotExist:
            raise ValidationError("Payment not found.")
        if not user.is_staff and payment.order.user != user:
            raise PermissionDenied("You don't have permission to refund this payment.")

        if not payment.can_be_refunded:
            raise ValidationError(
                f"Cannot refund payment with status: {payment.status}. "
                f"Only successful payments can be refunded."
            )

        refund_params: Dict[str, Any] = {
            'payment_intent': payment.stripe_payment_intent_id,
        }
        if amount:
            if amount > payment.amount:
                raise ValidationError(
                    f"Refund amount ({amount}) cannot exceed payment amount ({payment.amount})."
                )
            refund_params['amount'] = PaymentService._convert_to_stripe_amount(
                amount, payment.currency
            )

        if reason:
            valid_reasons = ['duplicate', 'fraudulent', 'requested_by_customer']
            if reason not in valid_reasons:
                raise ValidationError(
                    f"Invalid refund reason. Must be one of: {', '.join(valid_reasons)}"
                )
            refund_params['reason'] = reason

        try:
            refund = stripe.Refund.create(**refund_params)
            payment.status = Payment.Status.REFUNDED
            payment.save(update_fields=['status', 'updated_at'])
            PaymentService._cancel_order_and_restore_stock(
                payment.order_id, reason='payment refunded'
            )

            logger.info(
                f"Refunded payment {payment_id}: "
                f"{'full' if not amount else f'partial ({amount})'}"
            )
            return {
                'payment': payment,
                'refund': refund,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error refunding payment {payment_id}: {e}")
            raise ValidationError(f"Could not process refund: {e.user_message}")


class StripeWebhookService:

    @staticmethod
    def verify_webhook(payload: bytes, sig_header: str) -> stripe.Event:
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET

        if not webhook_secret:
            logger.warning("STRIPE_WEBHOOK_SECRET not configured!")
            raise ValidationError("Webhook secret not configured.")

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
            logger.debug(f"Verified webhook event: {event.type}")
            return event
        except ValueError as e:
            logger.warning(f"Invalid webhook payload: {e}")
            raise ValidationError("Invalid webhook payload.")
        except stripe.error.SignatureVerificationError as e:
            logger.warning(f"Webhook signature verification failed: {e}")
            raise ValidationError("Invalid webhook signature.")

    @staticmethod
    @transaction.atomic
    def handle_event(event: stripe.Event) -> Dict[str, Any]:
        event_type = event.type
        event_data = event.data.object

        logger.info(f"Processing webhook event: {event_type}")

        handlers = {
            'payment_intent.succeeded': StripeWebhookService._handle_payment_succeeded,
            'payment_intent.payment_failed': StripeWebhookService._handle_payment_failed,
            'payment_intent.canceled': StripeWebhookService._handle_payment_canceled,
            'charge.refunded': StripeWebhookService._handle_charge_refunded,
        }

        handler = handlers.get(event_type)

        if handler:
            return handler(event_data)
        else:
            logger.debug(f"Unhandled event type: {event_type}")
            return {
                'status': 'ignored',
                'message': f"Event type '{event_type}' is not handled."
            }

    @staticmethod
    @transaction.atomic
    def _handle_payment_succeeded(payment_intent) -> Dict[str, Any]:
        payment_intent_id = payment_intent.id

        try:
            payment = Payment.objects.select_for_update().get(
                stripe_payment_intent_id=payment_intent_id
            )
        except Payment.DoesNotExist:
            logger.warning(f"Payment not found for intent: {payment_intent_id}")
            return {
                'status': 'skipped',
                'message': f"Payment not found for intent {payment_intent_id}"
            }

        if payment.is_successful:
            logger.info(f"Payment {payment.id} already marked as succeeded, skipping")
            return {
                'status': 'skipped',
                'message': f"Payment {payment.id} already succeeded"
            }

        payment.status = Payment.Status.SUCCEEDED
        payment.save(update_fields=['status', 'updated_at'])

        order = Order.objects.select_for_update().get(id=payment.order_id)
        if order.status == Order.Status.PENDING:
            try:
                OrderService.update_order_status(order, Order.Status.PROCESSING)
                logger.info(f"Order {order.id} status updated to PROCESSING")
            except ValidationError as e:
                logger.warning(f"Could not update order status: {e}")
        elif order.status == Order.Status.PROCESSING:
            logger.info(
                f"Order {order.id} already in PROCESSING status, "
                f"no transition needed after payment success"
            )
        else:
            logger.warning(
                f"Order {order.id} in unexpected status '{order.status}' "
                f"after payment success"
            )

        logger.info(f"Payment {payment.id} marked as succeeded")
        return {
            'status': 'processed',
            'message': f"Payment {payment.id} succeeded for order {payment.order_id}"
        }

    @staticmethod
    @transaction.atomic
    def _handle_payment_failed(payment_intent) -> Dict[str, Any]:
        payment_intent_id = payment_intent.id

        try:
            payment = Payment.objects.select_for_update().get(
                stripe_payment_intent_id=payment_intent_id
            )
        except Payment.DoesNotExist:
            logger.warning(f"Payment not found for intent: {payment_intent_id}")
            return {
                'status': 'skipped',
                'message': f"Payment not found for intent {payment_intent_id}"
            }

        payment.status = Payment.Status.FAILED
        if payment_intent.last_payment_error:
            payment.failure_message = payment_intent.last_payment_error.get('message', 'Payment failed')
        else:
            payment.failure_message = 'Payment failed'

        payment.save(update_fields=['status', 'failure_message', 'updated_at'])
        logger.warning(f"Payment {payment.id} failed: {payment.failure_message}")
        return {
            'status': 'processed',
            'message': f"Payment {payment.id} marked as failed"
        }

    @staticmethod
    @transaction.atomic
    def _handle_payment_canceled(payment_intent) -> Dict[str, Any]:
        payment_intent_id = payment_intent.id

        try:
            payment = Payment.objects.select_for_update().get(
                stripe_payment_intent_id=payment_intent_id
            )
        except Payment.DoesNotExist:
            logger.warning(f"Payment not found for intent: {payment_intent_id}")
            return {
                'status': 'skipped',
                'message': f"Payment not found for intent {payment_intent_id}"
            }

        payment.status = Payment.Status.CANCELLED
        payment.save(update_fields=['status', 'updated_at'])

        PaymentService._cancel_order_and_restore_stock(
            payment.order_id, reason='payment cancelled via webhook'
        )

        logger.info(f"Payment {payment.id} cancelled via webhook")
        return {
            'status': 'processed',
            'message': f"Payment {payment.id} cancelled"
        }

    @staticmethod
    @transaction.atomic
    def _handle_charge_refunded(charge) -> Dict[str, Any]:
        payment_intent_id = charge.payment_intent

        if not payment_intent_id:
            logger.debug("Charge without payment_intent, skipping")
            return {
                'status': 'skipped',
                'message': "Charge without associated PaymentIntent"
            }
        try:
            payment = Payment.objects.select_for_update().get(
                stripe_payment_intent_id=payment_intent_id
            )
        except Payment.DoesNotExist:
            logger.warning(f"Payment not found for intent: {payment_intent_id}")
            return {
                'status': 'skipped',
                'message': f"Payment not found for intent {payment_intent_id}"
            }

        if charge.refunded:
            payment.status = Payment.Status.REFUNDED
            payment.save(update_fields=['status', 'updated_at'])
            logger.info(f"Payment {payment.id} marked as refunded")
        return {
            'status': 'processed',
            'message': f"Refund processed for payment {payment.id}"
        }
