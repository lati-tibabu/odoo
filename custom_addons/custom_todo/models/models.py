from odoo import models, fields, api

class TodoTask(models.Model):
    _name = "todo.task"
    _description = "Todo Task"

    name = fields.Char(string="Task", required=True)
    description = fields.Text(string="Description")
    is_done = fields.Boolean(string="Done", default=False)
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string="Priority", default='medium')
    due_date = fields.Date(string="Due Date")
    category = fields.Char(string="Category")
    create_date = fields.Datetime(string="Created", readonly=True)
    done_date = fields.Datetime(string="Completed", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'is_done' in vals and vals['is_done']:
                vals['done_date'] = fields.Datetime.now()
        return super().create(vals_list)

    def write(self, vals):
        if 'is_done' in vals:
            if vals['is_done']:
                vals['done_date'] = fields.Datetime.now()
            else:
                vals['done_date'] = False
        return super().write(vals)
