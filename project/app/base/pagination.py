

class Pagination(object):

    def __init__(self, curr_page, total_pages):
        self.curr_page = curr_page
        self.total_pages = total_pages

    @property
    def has_prev(self):
        return self.curr_page > 1

    @property
    def has_next(self):
        return self.curr_page < self.total_pages

    def iter_pages(self, left_edge=1, left_current=2,
                   right_current=5, right_edge=1):
        last = 0
        for num in xrange(1, self.total_pages+1):
            if num <= left_edge or \
               (num > self.curr_page - left_current - 1 and \
                num < self.curr_page + right_current) or \
               num > self.total_pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num


