class KardexConfig:
    _instance = None
    letInvoiceWithNegative: bool = False
    followTransaction: bool = True

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KardexConfig, cls).__new__(cls)
        return cls._instance
