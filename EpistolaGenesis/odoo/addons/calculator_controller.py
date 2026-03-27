from odoo import http
from odoo.http import request

class CalculatorController(http.Controller):
    
    @http.route('/calculator/calculate', type='json', auth='public', methods=['POST'])
    def calculate(self, num1, num2, operation):
        try:
            num1, num2 = float(num1), float(num2)
            if operation == "add":
                result = num1 + num2
            elif operation == "subtract":
                result = num1 - num2
            elif operation == "multiply":
                result = num1 * num2
            elif operation == "divide":
                if num2 == 0:
                    return {"error": "Division by zero is not allowed"}
                result = num1 / num2
            else:
                return {"error": "Invalid operation"}
            return {"result": result}
        except ValueError:
            return {"error": "Invalid numbers"}
