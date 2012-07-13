from public.views import report
from models import Votes


def test_return100_base():

    get = report()
    _sum = get['p1']+get['p2']

    assert _sum == 100, _sum


def test_add_one_vote_and_return_100():

    add = Votes()
    add['result'] = 1
    add.save()

    get = report()
    _sum = get['p1']+get['p2']
    assert _sum == 100, _sum


def test_add_three_vote_and_return_100():

    for a in [1,2,1]:
        add = Votes()
        add['result'] = a
        add.save()

    get = report()
    _sum = get['p1']+get['p2']
    assert _sum == 100, _sum


def test_not_assert_different_100():

    get = report()
    _sum = get['p1']+get['p2']
    assert _sum != 99, _sum
