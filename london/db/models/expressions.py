class Expression(object):
    def __init__(self, expression):
        self.expression = expression

class AggregationExpression(Expression):
    pass

class Sum(AggregationExpression):
    pass

class Count(AggregationExpression):
    pass

class Min(AggregationExpression):
    pass

class Max(AggregationExpression):
    def __init__(self, expression, distinct=False):
        self.distinct = distinct
        super(Max, self).__init__(expression)

class Average(AggregationExpression):
    pass

