+++
title = 'Decorators in Python'
date = 2024-05-06T21:21:51+02:00
+++

Python is renowned for its exceptional versatility, making it ideal for diverse applications, from web development to data science. In this blog post, we're diving into a powerful feature known as Decorators. Although I had not explored Decorators for quite some time, I decided it was finally time to thoroughly understand and master them.


## Understanding Nested Functions in Python
Before diving into decorators, it's helpful to understand nested functions in Python. A nested function is defined within another function, and it can access variables from the enclosing scope. Here’s an example to illustrate this:

```python
def outer(x):
    def inner(y):
        return x + y
    return inner
```

In the example above, inner is a nested function that adds a given number y to x, which is a parameter of the outer function outer. The nested function inner is only created and accessible within the outer function, not outside of it.

Here's how to use these functions:

```python
adding = outer(9) # At this moment, the outer function is initialized with the argument 5.
result = adding(10) # now we initilize the inner function with argument 6
print(result) # Result: 19
```

Nested functions are valuable for several reasons:

- Encapsulation: They help keep parts of code tightly coupled and hidden from the global scope.
- Scope Management: They can manipulate variables from their enclosing scope.
- Factory Functions: They can be used to create specific types of functions dynamically.
- Closures: They allow the inner function to remember the state of its environment, even after the outer function has finished executing.

## Decoding Decorators

Moving from nested functions to decorators, a decorator in Python is essentially a function that takes another function and extends its behavior without permanently modifying it. This is a fundamental concept in Python, especially useful in scenarios like logging, access control, memoization, and more.

```python

def my_decorator(func):
    def wrapper():
        print("Something happens before func execution")
        func()
        print("Something happens after func execution")
    return wrapper

@my_decorator
def say_hello():
    print("Hello, World!")
```

Unlike Nested Functions, Decorators are specifically built to enhance or modify the behaviour of other functions. They provide a clear, readable way to apply common functionality to multiple functions or methods, while nested functions can only serve function described within. 

## Properties

Decorators have certain properties that should be noted. Understanding these allows us to extract more value from using decorators.

### Stacking
Decorators can be stacked, meaning one function can have more than one decorator. Each decorator wraps the function return by the decorator beneath it. This is particularly useful for combining functionalities such as logging, error handling and access control in a modular way

```python
@decorator2
@decorator1
def some_function():
    return None
```

When stacking decorators, the decorator closest to the function definition runs first as a wrapper, but last in execution flow around the function call itself. This is beacuse each decorator wraps the result of the previous decorator.

```goat
# GoAT Diagram to Illustrate Stacked Decorators in Python

[Function] -> [Decorator1] : function is wrapped by decorator1
[Decorator1] -> [Decorator2] : decorator1 is wrapped by decorator2
[Function] -> [Decorator1] : Executes first
[Decorator1] -> [Decorator2] : Executes next

# Order of Execution: function -> decorator1 -> decorator2

```



### Parameterization
Decorators can be designed to take arguments. This requires the creation of a *decorator factory*, which returns a decorator. This is useful when you need to customize the behavior of the decorator for different functions:
```python
def repeat(number_of_times):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(number_of_times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(number_of_times=3)
def greet(name):
    print(f"Hello {name}")

greet("Alice")
```

### Metadata Preserverance
By default decorators do not keep a function's metadata (name, docstring and annotations). This is typically achieved using `functools.wraps` in the decorator's wrapper function:
```python
import functools

def my_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """Wrapper function"""
        print("Something is happening before the function is called.")
        return func(*args, **kwargs)
    return wrapper

@my_decorator
def say_hello():
    """Say hello function"""
    print("Hello!")

print(say_hello.__name__)  # Outputs 'say_hello'
print(say_hello.__doc__)   # Outputs 'Say hello function'
```

### Non-Functional Decorators (Class Decorators)
Decorators aren't limited to functions; they can also be used to be applied to classes. Class decorators can modify or enhance class behavior in a similar way to function decorators:

```python
def decorator(cls):
    class WrappedClass(cls):
        def new_method(self):
            return "This is a new method added by the decorator"
    return WrappedClass

@decorator
class OriginalClass:
    def original_method(self):
        return "This method is part of the original class"

obj = OriginalClass()
print(obj.new_method())  # Outputs: This is a new method added by the decorator

```


## Usage


### Function Decorators

Decorators should be used when there is several functions that need to share common functionality, avoiding code duplication. For example, a great use case is logging and debugging the execution of a program. Decorators can be used to log entry, exit and various states of function execution without cluttering the actual business logic with logging code.

```python
def log_execution(func):
    def wrapper(*args, **kwargs):
        print(f"Entering {func.__name__}...")
        result = func(*args, **kwargs)
        print(f"Exiting {func.__name__}...")
        print(f"Execution status: {result}")
        return result
    return wrapper

@log_execution
def my_function():
    # function code here
    pass
```

Another use case is the usage of Decorators as performance measurement. A decorator can be developed to add timing code that records how long a functions takes to run. 

```python 
import time

def measure_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Function {func.__name__} took {execution_time} seconds to run.")
        return result
    return wrapper

@measure_time
def my_function():
    # function code here
    pass

```

Certain function will require a finer access control and authentication policies. A decorator can be used to add this to certain function, ensuring that only authorized users are able to execute ceratin functionalities. This is common in web frameworks where ceratin routes or actions are restricted to logged-in users or users with specific roles.

```python
# Simulating a user database and session
users = {
    'alice': 'password123',
    'bob': 'securepassword'
}

current_user = None

def login(username, password):
    """ Simulate user login, setting the current user if successful. """
    global current_user
    if username in users and users[username] == password:
        current_user = username
        print(f"{username} has logged in successfully.")
        return True
    print("Failed login attempt.")
    return False

def logout():
    """ Log out the current user """
    global current_user
    current_user = None
    print("User has been logged out.")

def is_logged_in():
    """ Check if there's a user logged in """
    return current_user is not None

def login_required(func):
    """ Decorator to ensure the user is logged in before calling the function """
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            raise Exception("You must be logged in to access this function.")
        return func(*args, **kwargs)
    return wrapper

@login_required
def protected_function():
    """ Function that only executes if the user is authenticated """
    print(f"Access granted to {current_user}. Running protected function.")

# Example usage
login('alice', 'password123')  # Log in the user
protected_function()           # Should work as the user is logged in
logout()                       # Log out the user
try:
    protected_function()       # Should raise an exception as the user is not logged in
except Exception as e:
    print(e)
```

Another useful use-case is the use of decorators as input validating, which can be used to check the arguments apssed to a function before being executed. This helps maintaining clean and error-free data processing within functions

```python
def validate_inputs(func):
    """ Decorator to validate that inputs to the function are positive numbers. """
    def wrapper(*args, **kwargs):
        # Check all positional arguments
        for arg in args:
            if not isinstance(arg, (int, float)) or arg <= 0:
                raise ValueError("All dimensions must be positive numbers.")
        # Check all keyword arguments
        for value in kwargs.values():
            if not isinstance(value, (int, float)) or value <= 0:
                raise ValueError("All dimensions must be positive numbers.")
        return func(*args, **kwargs)
    return wrapper

@validate_inputs
def calculate_area(length, width):
    """ Calculate the area of a rectangle given length and width, both must be positive numbers. """
    return length * width

# Example usage
try:
    print("Area:", calculate_area(5, 10))  # Valid input
    print("Area:", calculate_area(-5, 10))  # This should raise an exception
except ValueError as e:
    print(e)

try:
    print("Area:", calculate_area(length=5, width=3))  # Valid input
    print("Area:", calculate_area(length=5, width=-3))  # This should raise an exception
except ValueError as e:
    print(e)
```

Decorators can also be leverage as abastract caching mechanism. Any function that is decorated with this caching function can have their results cached before being returned. The following example displays how this caching mechanism can be used with a fibonnaci function. Before the decorated function is executed, the decorator retrieves any data that is cached and passes to the fibonnaci function.

```python
def memorize(func):
    """ Decorator that caches the results of the function calls. """
    cache = {}  # Cache to store results of expensive function calls
    def wrapper(*args):
        if args in cache:
            return cache[args]  # Return cached result if available
        result = func(*args)  # Calculate result since it's not cached
        cache[args] = result  # Store the new result in cache
        return result
    return wrapper

@memorize
def fibonacci(n):
    """ Recursive function to calculate the nth Fibonacci number. """
    if n in (0, 1):  # Base cases
        return n
    return fibonacci(n-1) + fibonacci(n-2)  # Recursive call

# Example usage
print(f"Fibonacci 10: {fibonacci(10)}")  # This should compute and then cache all values up to Fib(10)
print(f"Fibonacci 20: {fibonacci(20)}")  # This should use cached values for Fib(0) to Fib(10) and compute the rest
```

Decorators could be used to enrich metadata by appending additional information to the output of a function. The following example displays a nested decorator, which enriches the output of the decorated function.

```python
def enrich_output(unit):
    """ Decorator to enrich function outputs with additional data such as units. """
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)  # Get the original function result
            enriched_result = {
                'value': result,
                'units': unit
            }  # Enrich the output with additional information
            return enriched_result
        return wrapper
    return decorator

@enrich_output('square meters')
def calculate_area(length, width):
    """ Calculate the area of a rectangle given length and width. """
    return length * width

# Example usage
area = calculate_area(5, 10)
print(area)  # Output will be a dictionary with the area and the units
```

Flask uses decorators to handle events. When a request is done to a specific Flask endpoint, Flask treats the HTTP request and triggers an action described in the decorated function. Then, when the function finishes execution, it takes the output and transforms it into a HTTP response.

```python
import functools
import logging

# Setting up logging
logging.basicConfig(level=logging.INFO)

def event_notifier(func):
    """ Decorator to notify events when the function is called and after it completes. """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"Function {func.__name__} called with args: {args} and kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logging.info(f"Function {func.__name__} completed successfully with result: {result}")
            return result
        except Exception as e:
            logging.error(f"Function {func.__name__} raised an error: {e}")
            raise  # Re-raise the exception after logging it
    return wrapper

@event_notifier
def add_numbers(a, b):
    """ Adds two numbers and returns the result. """
    return a + b

@event_notifier
def fail_function():
    """ A function designed to fail to demonstrate error logging. """
    raise ValueError("Intentional error for demonstration.")

# Example usage
print("Result of add_numbers:", add_numbers(5, 10))  # Should log call and completion

try:
    fail_function()  # Should log the call and the error
except ValueError as e:
    print(f"Caught an error: {e}")
```

### Class Decorators

As explained before, decorators aren't restricted to functions, they can also be used to extend a class functionality. They can be used to extend the functionality of several classes with additional methods, or alter existing methods. This is commonly used in framewors or libraries where certain behaviors need to be standardized across multiple classes. Decorators should be used in lieu of inheritance where flexibility and reusability are needed, improving the seperation of concerns. They can be dynamically applyed, meaning, they are applied at runtime, depending on the conditions of the program's execution or configuration. 

```python
def add_logging(cls):
    class WrappedClass(cls):
        def log_method(self, method_name):
            print(f"Method {method_name} started")
            result = method_name()
            print(f"Method {method_name} ended")
            return result

        def __getattr__(self, name):
            attr = getattr(super(), name)
            if callable(attr):
                def wrapper(*args, **kwargs):
                    return self.log_method(lambda: attr(*args, **kwargs))
                return wrapper
            return attr
    return WrappedClass

@add_logging
class SomeClass:
    def method_one(self):
        print("Executing method one")

    def method_two(self):
        print("Executing method two")

obj = SomeClass()
obj.method_one()
```

Furthermore, decorators can be used to ensure that certain classes adhere to a defined interface or abstract base class without using inheritance. This is particularly useful in large systems adhering to strict architectural patterns where specific methods must be implemented by multiple classes:

```python
def ensure_interface(interface):
    def decorator(cls):
        missing_methods = [m for m in interface if not hasattr(cls, m)]
        if missing_methods:
            raise TypeError(f"Class {cls.__name__} does not implement {missing_methods}")
        return cls
    return decorator

@ensure_interface(['process', 'validate'])
class Processor:
    def process(self):
        pass  # Implement the required method
    # Validate method is intentionally missing to show the error

# This will raise a TypeError indicating the 'validate' method is missing.
```

Finally, decorators can be used to enforce the singleton pattern, limiting a class to a single instance throughout the lifetime of a program. This is commonly used in cases you need a controlled access point to a resrouce, such as a database connection or a configuration manager.

```python
def singleton(cls):
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

@singleton
class DatabaseConnection:
    def __init__(self):
        self.status = 'Connected'

# Both instances will actually be the same object
db1 = DatabaseConnection()
db2 = DatabaseConnection()
print(db1 is db2)  # Outputs: True
```