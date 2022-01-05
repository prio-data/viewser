
from views_schema import docs as schema
from viewser import crud_operations

class DocumentationCrudOperations(crud_operations.CrudOperations[
    schema.PostedDocumentationPage,
    schema.ViewsDoc,
    schema.ViewsDoc]):

    @property
    def __locations__(self):
        return {
            "main": f"docs/{self.path}"
        }

    @property
    def __listed_model__(self):
        raise AttributeError("DocumentationCrud does not have a listed_model")

    def __init__(self, base_url: str, path: str):
        self.path = path
        super().__init__(base_url)

    __posted_model__ = schema.PostedDocumentationPage
    __detail_model__ = schema.ViewsDoc

    def _check_post_exists(self,name: str)->bool:
        doc_page = self.show(name)
        if doc_page.page is None:
            return False
        else:
            return True

    def list(self) -> schema.ViewsDoc:
        return self.show("")
