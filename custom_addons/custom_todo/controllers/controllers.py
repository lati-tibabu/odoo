from odoo import http
from odoo.http import request

class TodoController(http.Controller):

    @http.route("/todo", type="http", auth="user", website=False)
    def todo_list(self, filter='all'):
        domain = []
        if filter == 'pending':
            domain = [('is_done', '=', False)]
        elif filter == 'done':
            domain = [('is_done', '=', True)]
        tasks = request.env["todo.task"].search(domain, order="create_date desc")
        return request.render(
            "custom_todo.todo_page",
            {
                "tasks": tasks,
                "filter": filter,
                "request": request,
            }
        )

    @http.route(
        "/todo/add",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=True,
    )
    def todo_add(self, **post):
        name = post.get("name")
        description = post.get("description", "")
        priority = post.get("priority", "medium")
        due_date = post.get("due_date") or False
        category = post.get("category", "")
        if name:
            request.env["todo.task"].create({
                "name": name.strip(),
                "description": description.strip(),
                "priority": priority,
                "due_date": due_date,
                "category": category.strip(),
            })
        return request.redirect("/todo")

    @http.route(
        "/todo/toggle/<int:task_id>",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=True,
    )
    def todo_toggle(self, task_id, **post):
        task = request.env["todo.task"].browse(task_id)
        if task.exists():
            task.is_done = not task.is_done
        return request.redirect("/todo")

    @http.route(
        "/todo/delete/<int:task_id>",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=True,
    )
    def todo_delete(self, task_id, **post):
        task = request.env["todo.task"].browse(task_id)
        if task.exists():
            task.unlink()
        return request.redirect("/todo")

    @http.route(
        "/todo/edit/<int:task_id>",
        type="http",
        auth="user",
        methods=["GET", "POST"],
        csrf=True,
    )
    def todo_edit(self, task_id, **post):
        task = request.env["todo.task"].browse(task_id)
        if not task.exists():
            return request.redirect("/todo")
        
        if request.httprequest.method == 'POST':
            name = post.get("name")
            description = post.get("description", "")
            priority = post.get("priority", "medium")
            due_date = post.get("due_date") or False
            category = post.get("category", "")
            if name:
                task.write({
                    "name": name.strip(),
                    "description": description.strip(),
                    "priority": priority,
                    "due_date": due_date,
                    "category": category.strip(),
                })
            return request.redirect("/todo")
        
        return request.render(
            "custom_todo.todo_edit_page",
            {
                "task": task,
                "request": request,
            }
        )
