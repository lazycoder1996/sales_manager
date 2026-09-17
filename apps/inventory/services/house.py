from apps.inventory.models import House


class HouseService:

    @staticmethod
    def get_houses():
        return (
            House.objects
            .select_related("partner_house")
            .all()
        )

    @staticmethod
    def get_house(house_id):
        return (
            House.objects
            .select_related("partner_house")
            .filter(id=house_id)
            .first()
        )