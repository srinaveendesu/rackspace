import faust


class Company(faust.Record):
    name: str
    domain: str

class Domain_information(faust.Record, serializer='json'):
    clearbitData: str
    name: str