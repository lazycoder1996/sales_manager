from apps.inventory.models import Product


class ProductService:

    @staticmethod
    def create(
        name,
        cost_price,
        selling_price,
        required=True,
        required_quantity=1,
    ):
        return Product.objects.create(
            name=name,
            cost_price=cost_price,
            selling_price=selling_price,
            required=required,
            required_quantity=required_quantity,
        )

    @staticmethod
    def update(
        product,
        name=None,
        cost_price=None,
        selling_price=None,
        required=None,
        required_quantity=None,
    ):
        update_fields = []

        if name is not None:
            product.name = name
            update_fields.append("name")

        if cost_price is not None:
            product.cost_price = cost_price
            update_fields.append("cost_price")

        if selling_price is not None:
            product.selling_price = selling_price
            update_fields.append("selling_price")

        if required is not None:
            product.required = required
            update_fields.append("required")

        if required_quantity is not None:
            product.required_quantity = required_quantity
            update_fields.append("required_quantity")

        if update_fields:
            update_fields.append("updated_at")

            product.save(
                update_fields=update_fields
            )

        return product

    @staticmethod
    def activate(product):
        if product.is_active:
            return product

        product.is_active = True

        product.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        return product

    @staticmethod
    def deactivate(product):
        if not product.is_active:
            return product

        product.is_active = False

        product.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        return product