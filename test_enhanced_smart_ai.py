#!/usr/bin/env python3
"""
Test script for the enhanced Smart AI CLI v2
"""

def calculator(a, b, operation):
    """Simple calculator function"""
    if operation == 'add':
        return a + b
    elif operation == 'subtract':
        return a - b
    elif operation == 'multiply':
        return a * b
    elif operation == 'divide':
        if b != 0:
            return a / b
        else:
            raise ValueError("Cannot divide by zero")
    else:
        raise ValueError("Invalid operation")

class MathHelper:
    """Helper class for mathematical operations"""
    
    def __init__(self):
        self.history = []
    
    def add_to_history(self, operation, result):
        """Add operation to history"""
        self.history.append(f"{operation} = {result}")
    
    def get_history(self):
        """Get calculation history"""
        return self.history

if __name__ == "__main__":
    helper = MathHelper()
    result = calculator(5, 3, 'add')
    helper.add_to_history("5 + 3", result)
    print(f"Result: {result}")
    print(f"History: {helper.get_history()}")