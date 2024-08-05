class Context:
    def __init__(self, router_context=None, ui_context=None):
        self.router_context = router_context or {}
        self.ui_context = ui_context or {}
