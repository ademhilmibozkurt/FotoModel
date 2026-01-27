from infra.database import SupabaseDB

class SelectionOps:
    def __init__(self, tab):
        self.tab = tab

        self.supabase = SupabaseDB()

    def refresh_tree(self, data):
        self.tab.tree.delete(*self.tab.tree.get_children())

        if not data:
            return

        columns = list(data[0].keys())

        # add is_completed state
        if "Durum" not in columns:
            columns.insert(0, "Durum")

        self.tab.tree["columns"] = columns
        self.tab.tree["show"] = "headings"

        for col in columns:
            self.tab.tree.heading(col, text=col)
            self.tab.tree.column(col, width=50)

        # for show selected templates in new window
        self.tree_record_map = {}
        for row in data:
            completed = row.get("is_completed", False)
            status_text = "✔" if completed else "⬜"
            
            values = [status_text] + list(row.values())

            item_id = self.tab.tree.insert("", "end", values=values)
            self.tree_record_map[item_id] = row

    def filter_tree(self, *args):
        query = self.tab.search_var.get().lower()

        if not query:
            self.refresh_tree(self.tab.all_data)
            return

        filtered = [
            row for row in self.tab.all_data
            if any(query in str(v).lower() for v in row.values())
        ]

        self.refresh_tree(filtered)

    # on single click update is_completed state
    def on_tree_single_click(self, event):
        region = self.tab.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.tab.tree.identify_column(event.x)
        if column != "#1":
            return

        row_id = self.tab.tree.identify_row(event.y)
        if not row_id:
            return

        values = list(self.tab.tree.item(row_id, "values"))
        current = values[0]

        new_value = "✔" if current == "⬜" else "⬜"
        values[0] = new_value
        self.tab.tree.item(row_id, values=values)

        record = self.tree_record_map.get(row_id)
        if record:
            self.supabase.update_completed_status(record, new_value == "✔")

    # on double click open new window for show selected images
    def on_tree_double_click(self, event):
        selected = self.tab.tree.selection()
        if not selected:
            return

        item_id = selected[0]
        record = self.tree_record_map.get(item_id)

        if not record:
            return

        self.tab.open_selection_detail(record)