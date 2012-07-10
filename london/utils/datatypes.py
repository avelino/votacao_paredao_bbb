from decimal import Decimal

from london.conf import settings
from london.utils.formats import number_format, get_format

try:
    from money import Money as OriginalMoney
except ImportError:
    OriginalMoney = Decimal

class Money(OriginalMoney):
    amount = 0
    def __init__(self, amount=Decimal("0.0"), currency=None):
        if isinstance(amount, OriginalMoney):
            try:
                amount = amount.amount
            except AttributeError: # just in case python-money is not installed (Decimal assumes as OriginalMoney)
                pass
        currency = currency or settings.DEFAULT_CURRENCY

        if OriginalMoney == Decimal:
            OriginalMoney.__init__(self, amount)
            self.amount = amount
            self.currency = currency
        else:
            OriginalMoney.__init__(self, str(amount).replace(get_format('THOUSAND_SEPARATOR'),''), currency)

    def __str__(self):
        return number_format(self.amount, decimal_pos=get_format('DECIMAL_PLACES'))

    def __unicode__(self):
        return unicode(str(self))

    def __float__(self):
        return float(self.amount)

    def __nonzero__(self):
        return bool(self.amount)

    def __eq__(self, other):
        if other is None:
            return False
        if isinstance(other, Money):
            return (self.amount == other.amount) and (self.currency == other.currency)
        return self.amount == Decimal(str(other).replace(get_format('THOUSAND_SEPARATOR'),''))

    def __pos__(self):
        return Money(OriginalMoney.__pos__(self))

    def __neg__(self):
        return Money(OriginalMoney.__neg__(self))

    def __add__(self, other):
        return Money(OriginalMoney.__add__(self, other))

    def __sub__(self, other):
        return Money(OriginalMoney.__sub__(self, other))

    def __mul__(self, other):
        return Money(OriginalMoney.__mul__(self, other))

    def __div__(self, other):
        return Money(OriginalMoney.__div__(self, other))

    def __rmod__(self, other):
        return Money(OriginalMoney.__rmod__(self, other))

    __radd__ = __add__
    __rsub__ = __sub__
    __rmul__ = __mul__
    __rdiv__ = __div__
    
    def convert_to_default(self):
        return Money(OriginalMoney.convert_to_default(self))

