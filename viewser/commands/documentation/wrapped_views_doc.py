
from views_schema import docs as schema

class WrappedViewsDoc:
    def __init__(self, doc: schema.ViewsDoc):
        self.doc = doc

    @property
    def name(self):
        return self.doc.entry.name

    @property
    def heading(self):
        return self.name.capitalize()

    @property
    def has_page(self):
        return self.doc.page is not None

    @property
    def description(self):
        return self.doc.page.content if self.has_page else "No description added"

    @property
    def author(self):
        return self.doc.page.author if self.has_page else None

    @property
    def date_updated(self):
        return str(self.doc.page.last_edited.date()) if self.has_page else None

    @property
    def sub_entries(self):
        return self.doc.entry.entries

    @property
    def data(self):
        return self.doc.entry.data

    def json(self):
        return self.doc.json()
