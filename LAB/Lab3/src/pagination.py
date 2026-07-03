"""A small class that divides a list into pages."""


class Paginator:
    def __init__(self, items, page_size=20):
        if page_size <= 0:
            raise ValueError("page_size must be greater than zero")
        self.items = items
        self.page_size = page_size

    def pages(self):
        result = []
        for start in range(0, len(self.items), self.page_size):
            result.append(self.items[start : start + self.page_size])
        return result
