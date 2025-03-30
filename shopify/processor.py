from shopify.models import Order, Customer, Shop


def extract_shopify_data(webhook_payload, shop_domain, shop_id):

    shop = Shop(shop_id=shop_id,
                domain=shop_domain,
                email="test@gmail.com")
    if not Shop.objects.filter(domain=shop_domain).exists():
        shop.save()
        print(f'Saved Shop object.')

    order = Order(name=webhook_payload.get("name"),
                  order_id=webhook_payload.get("id"),
                  total_price=webhook_payload.get("current_total_price"),
                  domain=shop,
                  app_id=webhook_payload.get("app_id"),
                  payload=webhook_payload,
                  customer_email=webhook_payload.get("email"))
    if not Order.objects.filter(order_id=webhook_payload.get("id"), domain=shop_domain).exists():
        order.save()
        print(f'Saved Order object.')

    return [shop, order]

    # customer_data = webhook_payload.get("customer")
    # if Customer.objects.filter(shop_customer_id=customer_data.get("id"), domain=shop).exists() is False:
    #    customer = Customer(shop_customer_id=customer_data.get("id"),
    #                       domain=shop,
    #                      email=customer_data.get("email"),
    #                     first_name=customer_data.get("first_name"),
    #                    last_name=customer_data.get("last_name"),
    #                   verified_email=customer_data.get("verified_email")
    #                  )
    # customer.save()
    # print(f'Saved Customer object.')
