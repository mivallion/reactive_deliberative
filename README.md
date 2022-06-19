# reactive_deliberative

## Introduction

The reactive_deliberative project allows creating applications
with a reactive-deliberative architecture.

The hybrid deliberative-reactive architecture arose as a result of the recognition
that there is a use of symbolic knowledge in describing the behavior of an intelligent agent.

Such an architecture allows an agent with reactive behavior to flexibly adjust 
its behavior due to a high-level scheduler in accordance with the current task, 
while at the same time taking into account the state of the environment. For 
the agent, which is a kind of intelligent system, it will provide an opportunity 
to respond to unplanned environmental changes.

In simple words, the agent follows the behavior described in the rules, interrupting for reactive actions.

![architecture](./img/1.png)

This system is built using one the implementation of the Rete algorithms - [py_rete][py_rete].

## Installation

This package is installable via pip with the following command:
`pip install -U reactive_deliberative`.

## The Basics

The two high-level structures to support reasoning with py_rete are **facts**
and **productions**. 

### Facts

Facts represent the basic units of knowledge that the productions match over.
Here are a few examples of facts and how they work.

1. *Facts* are a subclass of dict, so you can treat them similar to dictionaries.

```python
>>> f = Fact(a=1, b=2)
>>> f['a']
1
```

2. *Facts* extend dictionaries, so they also support positional values without
   keys. These values are assigned numerical indices based on their position.

```python
>>> f = Fact('a', 'b', 'c')
>>> f[0]
'a'
```

3. *Facts* can support mixed positional and named arguments, but positional
   must come before named and named arguments do not get positional references.

```python
>>> f = Fact('a', 'b', c=3, d=4)
>>> f[0]
'a'
>>> f['c']
3
```

5. *Facts* support nesting with other facts. 

```python
>>> f = Fact(subfact=Fact())
Fact(subfact=Fact())
```

Note that there will be issues if facts contain other data structures that
contain facts (they will not be properly added to the rete network or to
productions).

### Productions

*Productions* have two components:
* Conditions, which are essentially facts that can contain pattern matching
  variables.
* A Function, which is executed for each rule match, with the arguments to the
  function being passed the bindings from pattern matching variables.

Here is an example of a simple *Productions* that binds with all *Facts* that
have the color red and prints 'I found something red' for each one:

```python
@Production(Fact(color='red'))
def alert_something_red():
    print("I found something red")
```

Productions also support logical operators to express more complex conditions.

```python
@Production(AND(OR(Fact(color='red'),
                   Fact(color='blue')),
	        NOT(Fact(color='green'))))
def alert_something_complex():
    print("I found something red or blue without any green present")
```

Bitwise logical operators can be used as shorthand to make composing complex conditions easier.
```python
@Production((Fact(color='red') | Fact(color='blue')) & ~Fact(color='green'))
def alert_something_complex2():
    print("I found something red or blue without any green present")
```

In addition to matching simple facts, pattern matching variables can be used to
match values from Facts. Matching ensures that variable bindings are consistent
across conditions. Additionally, variables are passed to arguments in the function
with the same name during matching. For example, the following production finds
a Fact with a lastname attribute.  For each Fact it finds, it prints "I found a
fact with a lastname attribute: `<lastname>`".  Note, the `V('lastname')`
corresponds to a variable named lastname that can bind with values from Facts
during matching.  Additionally the variable (`V('lastname')`) and the function
argument `lastname` match have the same name, which enables the matcher to the
variable bindings into the function.
```python
@Production(Fact(lastname=V('lastname')))
def found_relatives(lastname):
    print("I found a fact with a lastname: {}".format(lastname))
```

It is also possible to employ functional tests (lambdas or functions) using
`Filter` conditions. Like the function that is being decorated, Filter
conditions pass variable bindings to their equivelently named function
arguments. It is important to note that positive facts that bind with these
variables need to be listed in the production before the tests that use them.
```python
@Production(Fact(value=V('a')) &
            Fact(value=V('b')) &
            Filter(lambda a, b: a > b) &
            Fact(value=V('c')) &
            Filter(lambda b, c: b > c))
def three_values(a, b, c):
    print("{} is greater than {} is greater than {}".format(a, b, c))
```

It is also possible to bind *facts* to variables as well, using the bitshift
operator.
```python
@Production(V('name_fact') << Fact(name=V('name')))
def found_name(name_fact):
    print("I found a name fact {}".format(name_fact))
```

Productions can have priority and execution timeout:

```python
@Production(V('fact') << Fact(state="transform"), priority=2, timeout=1)
async def transform(net, fact):
...
```

Productions can be asynchronous:

```python
@Production(V('name_fact') << Fact(name=V('name')))
async def found_name(name_fact):
    print("I found a name fact {} and going to sleep".format(name_fact))
    await asyncio.sleep(10)
```

### ReactiveDeliberative

Here is how you create an engine:

```python
rd = ReactiveDeliberative()
```

Once an engine has been created, then facts can be added to it.
```python
f1 = Fact(light_color="red")
rd.add_fact(f1)
```

Note, facts added to the network cannot contain any variables or they will
trigger an exception when added. Additionally, once a fact has been added to
network it is assigned a unique internal identifier.

This makes it possible to update the fact.
```python
f1['light_color'] = "green"
net.update_fact(f1)
```

It also make it possible to remove the fact.
```python
rd.remove_fact(f1)
```

When updating a fact, note that it is not updated in the network until
the `update_fact` method is called on it. An update essentially equates to
removing and re-adding the fact.

Productions can also be added to the network. Productions also can make use of
the `net` variable, which is automatically bound to the Rete network the
production has been added to. This makes it possible for productions to update
the contents of the network when they are fired. For example, the following functions
have an argument called `net` that is bound to the rete network even though there is
no variable by that name in the production conditions.
```python
>>> f1 = Fact(light_color="red")
>>> 
>>> @Production(V('fact') << Fact(light_color="red"))
>>> def make_green(net, fact):
>>>	print('making green')
>>>     fact['light_color'] = 'green'
>>>     net.update_fact(fact)
>>> 
>>> @Production(V('fact') << Fact(light_color="green"))
>>> def make_red(net, fact):
>>>	print('making red')
>>>     fact['light_color'] = 'red'
>>>     net.update_fact(fact)
>>> 
>>> rd = ReactiveDeliberative()
>>> rd.add_fact(f1)
>>> rd.add_production(make_green)
>>> rd.add_production(make_red)
```

Once the above fact and productions have been added the network can be run in the infinite loop. 
```python
>>> rd.run()
making green
making red
making green
making red
making green
...
```

### Reactive predicates and actions

Predicate functions and action functions must be asynchronous.

The predicate function can contain any calls and calculations,
but it must return a Boolean value. If the predicate is executed,
a reactive action will be performed. For example:

```python
async def external_upload_predicate():
    return await dumper.external_upload_predicate()


async def external_upload_action():
    return await dumper.external_upload_action()
```

After declaring the function, you can add them to the engine:

```python
rd.add_reactive_action(external_upload_predicate, external_upload_action)
```

By default, predicate trigger stops the deliberative loop for the duration of the reactive action.
To disable this future pass `force=False` argument in `add_reactive_action`:
```python
rd.add_reactive_action(external_upload_predicate, external_upload_action, force=False)
```


[py_rete]: https://github.com/cmaclell/py_rete