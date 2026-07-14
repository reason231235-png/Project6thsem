from django.db import models


class TransactionStatus(models.TextChoices):
    INITIATE = "INITIATE", "Initiate"
    COMPLETE = "COMPLETE", "Complete"
    FAIL = "FAIL", "Fail"


class TransactionType(models.TextChoices):
    ESEWA = "ESEWA", "Esewa"
    KHALTI = "KHALTI", "Khalti"
