import stripe
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except stripe.error.SignatureVerificationError:
        return HttpResponseBadRequest("invalid signature")
    except Exception:
        return HttpResponseBadRequest("invalid payload")

    if event["type"] == "checkout.session.completed":
        # session = event["data"]["object"]
        # TODO: mark subscription active for customer (session['customer'])
        # and price (session['metadata'] or line_items)
        pass
    elif event["type"] == "customer.subscription.deleted":
        # TODO: mark subscription cancelled
        pass

    return HttpResponse(status=200)
