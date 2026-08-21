# 方法与初始化器

<!--
> When you are on the dancefloor, there is nothing to do but dance.
>
> <cite>Umberto Eco, <em>The Mysterious Flame of Queen Loana</em></cite>
-->
> 当你站在舞池上，除了跳舞别无他事。
>
> <cite>翁贝托·埃科，<em>《洛安娜女王的神秘火焰》</em></cite>

<!--
It is time for our virtual machine to bring its nascent objects to life with
behavior. That means methods and method calls. And, since they are a special
kind of method, initializers too.
-->
是时候让虚拟机给那些初生的对象注入行为了。也就是方法，以及方法调用。而初始化器——作为一类特殊方法——也一并登场。

<!--
All of this is familiar territory from our previous jlox interpreter. What's new
in this second trip is an important optimization we'll implement to make method
calls over seven times faster than our baseline performance. But before we get
to that fun, we gotta get the basic stuff working.
-->
这些在先前的 jlox 解释器里都是熟地。第二次旅程里真正新鲜的，是一项重要优化：我们会把方法调用做得比基线性能快七倍以上。不过在享用那份乐趣之前，得先把基础跑通。

<!--
-- Method Declarations
-->
## 方法声明

<!--
We can't optimize method calls before we have method calls, and we can't call
methods without having methods to call, so we'll start with declarations.
-->
没有方法调用，谈不上优化方法调用；没有可调用的方法，也谈不上调用。所以我们从声明开始。

<!--
-- Representing methods
-->
### 表示方法

<!--
We usually start in the compiler, but let's knock the object model out first
this time. The runtime representation for methods in clox is similar to that of
jlox. Each class stores a hash table of methods. Keys are method names, and each
value is an ObjClosure for the body of the method.
-->
我们通常从编译器下手，这次先把对象模型敲定。clox 里方法的运行时表示与 jlox 相似。每个类存一张方法哈希表：键是方法名，值是方法体对应的 ObjClosure。

^code class-methods (3 before, 1 after)

<!--
A brand new class begins with an empty method table.
-->
崭新的类从一张空方法表起步。

^code init-methods (1 before, 1 after)

<!--
The ObjClass struct owns the memory for this table, so when the memory manager
deallocates a class, the table should be freed too.
-->
ObjClass 结构体拥有这张表的内存，所以内存管理器释放类时，表也该一并释放。

^code free-methods (1 before, 1 after)

<!--
Speaking of memory managers, the GC needs to trace through classes into the
method table. If a class is still reachable (likely through some instance),
then all of its methods certainly need to stick around too.
-->
说到内存管理器：GC 需要从类追踪进方法表。若类仍可达（多半经由某个实例），它的全部方法当然也得留下。

^code mark-methods (1 before, 1 after)

<!--
We use the existing `markTable()` function, which traces through the key string
and value in each table entry.
-->
我们用现成的 `markTable()`：它会追踪表中每条条目的键字符串与值。

<!--
Storing a class's methods is pretty familiar coming from jlox. The different
part is how that table gets populated. Our previous interpreter had access to
the entire AST node for the class declaration and all of the methods it
contained. At runtime, the interpreter simply walked that list of declarations.
-->
从 jlox 过来，存类的方法相当眼熟。不同之处在于表如何填满。先前的解释器能拿到类声明的整个 AST 节点，以及其中全部方法。运行时，解释器只要走过那份声明列表。

<!--
Now every piece of information the compiler wants to shunt over to the runtime
has to squeeze through the interface of a flat series of bytecode instructions.
How do we take a class declaration, which can contain an arbitrarily large set
of methods, and represent it as bytecode? Let's hop over to the compiler and
find out.
-->
如今，编译器想塞给运行时的每一片信息，都得挤过平坦字节码指令序列这扇接口。一个类声明可以含任意多方法——我们如何把它表示成字节码？且跳到编译器那边看看。

<!--
-- Compiling method declarations
-->
### 编译方法声明

<!--
The last chapter left us with a compiler that parses classes but allows only an
empty body. Now we insert a little code to compile a series of method
declarations between the braces.
-->
上一章留给我们的编译器能解析类，但只允许空类体。现在我们插一点代码，在花括号之间编译一连串方法声明。

^code class-body (1 before, 1 after)

<!--
Lox doesn't have field declarations, so anything before the closing brace at the
end of the class body must be a method. We stop compiling methods when we hit
that final curly or if we reach the end of the file. The latter check ensures
our compiler doesn't get stuck in an infinite loop if the user accidentally
forgets the closing brace.
-->
Lox 没有字段声明，所以类体收尾花括号之前的任何东西都必须是方法。碰到那最后的花括号，或到了文件末尾，就停止编译方法。后一项检查保证：用户万一忘了写闭合花括号，编译器也不会陷进死循环。

<!--
The tricky part with compiling a class declaration is that a class may declare
any number of methods. Somehow the runtime needs to look up and bind all of
them. That would be a lot to pack into a single `OP_CLASS` instruction. Instead,
the bytecode we generate for a class declaration will split the process into a
<span name="series">*series*</span> of instructions. The compiler already emits
an `OP_CLASS` instruction that creates a new empty ObjClass object. Then it
emits instructions to store the class in a variable with its name.
-->
编译类声明的棘手处在于：一个类可以声明任意数量的方法。运行时总得想办法查找并绑定它们全部。塞进单条 `OP_CLASS` 指令会太挤。于是，我们为类声明生成的字节码会把过程拆成一<span name="series">*系列*</span>指令。编译器已经会发出创建空 ObjClass 的 `OP_CLASS`，接着再发出把类存进同名变量的指令。

<aside name="series">

<!--
We did something similar for closures. The `OP_CLOSURE` instruction needs to
know the type and index for each captured upvalue. We encoded that using a
series of pseudo-instructions following the main `OP_CLOSURE` instruction --
basically a variable number of operands. The VM processes all of those extra
bytes immediately when interpreting the `OP_CLOSURE` instruction.

Here our approach is a little different because from the VM's perspective, each
instruction to define a method is a separate stand-alone operation. Either
approach would work. A variable-sized pseudo-instruction is possibly marginally
faster, but class declarations are rarely in hot loops, so it doesn't matter
much.
-->
闭包也干过类似的事。`OP_CLOSURE` 需要知道每个被捕获上值的类型与索引。我们用跟在主 `OP_CLOSURE` 后面的一串伪指令来编码——本质上是可变数量的操作数。虚拟机解释 `OP_CLOSURE` 时会立刻处理那些额外字节。

这里做法稍有不同：从虚拟机视角看，每条定义方法的指令都是独立操作。两种路都能走。可变大小的伪指令或许略快一点，但类声明很少出现在热循环里，所以差别不大。

</aside>

<!--
Now, for each method declaration, we emit a new `OP_METHOD` instruction that
adds a single method to that class. When all of the `OP_METHOD` instructions
have executed, we're left with a fully formed class. While the user sees a class
declaration as a single atomic operation, the VM implements it as a series of
mutations.
-->
于是，对每个方法声明，我们发出一条新的 `OP_METHOD`，往那个类上加一个方法。全部 `OP_METHOD` 执行完，就留下一个成形完备的类。用户眼里类声明是一次原子操作，虚拟机却用一连串变更来实现它。

<!--
To define a new method, the VM needs three things:

1.  The name of the method.

1.  The closure for the method body.

1.  The class to bind the method to.

We'll incrementally write the compiler code to see how those all get through to
the runtime, starting here:
-->
要定义一个新方法，虚拟机需要三样东西：

1.  方法的名字。

1.  方法体的闭包。

1.  要把方法绑上去的那个类。

我们逐步写编译器代码，看看它们如何抵达运行时，从这里开始：

^code method

<!--
Like `OP_GET_PROPERTY` and other instructions that need names at runtime, the
compiler adds the method name token's lexeme to the constant table, getting back
a table index. Then we emit an `OP_METHOD` instruction with that index as the
operand. That's the name. Next is the method body:
-->
和 `OP_GET_PROPERTY` 以及其他运行时需要名字的指令一样，编译器把方法名 token 的词素加进常量表，拿回一个表索引。然后发出以该索引为操作数的 `OP_METHOD`。名字就位了。接下来是方法体：

^code method-body (1 before, 1 after)

<!--
We use the same `function()` helper that we wrote for compiling function
declarations. That utility function compiles the subsequent parameter list and
function body. Then it emits the code to create an ObjClosure and leave it on
top of the stack. At runtime, the VM will find the closure there.
-->
我们复用为编译函数声明写的那个 `function()` 辅助函数。它编译随后的参数列表与函数体，再发出创建 ObjClosure 并把它留在栈顶的代码。运行时，虚拟机就会在那儿找到闭包。

<!--
Last is the class to bind the method to. Where can the VM find that?
Unfortunately, by the time we reach the `OP_METHOD` instruction, we don't know
where it is. It <span name="global">could</span> be on the stack, if the user
declared the class in a local scope. But a top-level class declaration ends up
with the ObjClass in the global variable table.
-->
最后是要把方法绑上去的类。虚拟机上哪儿找它？不幸的是，走到 `OP_METHOD` 时，我们并不知道它在哪儿。若用户在局部作用域声明类，它<span name="global">可能</span>在栈上；但顶层类声明最终会把 ObjClass 放进全局变量表。

<aside name="global">

<!--
If Lox supported declaring classes only at the top level, the VM could assume
that any class could be found by looking it up directly from the global
variable table. Alas, because we support local classes, we need to handle that
case too.
-->
若 Lox 只允许在顶层声明类，虚拟机大可假定：随便哪个类都能直接从全局变量表查到。可惜我们支持局部类，那种情况也得处理。

</aside>

<!--
Fear not. The compiler does know the *name* of the class. We can capture it
right after we consume its token.
-->
别慌。编译器确实知道类的*名字*。消费完名字 token 后，我们立刻把它记下来。

^code class-name (1 before, 1 after)

<!--
And we know that no other declaration with that name could possibly shadow the
class. So we do the easy fix. Before we start binding methods, we emit whatever
code is necessary to load the class back on top of the stack.
-->
而且我们知道：不可能有别的同名声明把这个类影掉。于是走简单修补：开始绑定方法之前，发出把类重新加载到栈顶所需的一切代码。

^code load-class (2 before, 1 after)

<!--
Right before compiling the class body, we <span name="load">call</span>
`namedVariable()`. That helper function generates code to load a variable with
the given name onto the stack. Then we compile the methods.
-->
就在编译类体之前，我们<span name="load">调用</span>`namedVariable()`。那个辅助函数生成把给定名字的变量加载到栈上的代码。然后我们编译方法。

<aside name="load">

<!--
The preceding call to `defineVariable()` pops the class, so it seems silly to
call `namedVariable()` to load it right back onto the stack. Why not simply
leave it on the stack in the first place? We could, but in the [next
chapter][super] we will insert code between these two calls to support
inheritance. At that point, it will be simpler if the class isn't sitting around
on the stack.

[super]: superclasses.html
-->
前面的 `defineVariable()` 会把类弹出，再调用 `namedVariable()` 把它装回栈上看起来挺傻。何不一开始就留在栈上？可以，但在[下一章][super]我们会在这两次调用之间插入支持继承的代码。到那时，类若不杵在栈上，会更省事。

[super]: superclasses.html

</aside>

<!--
This means that when we execute each `OP_METHOD` instruction, the stack has the
method's closure on top with the class right under it. Once we've reached the
end of the methods, we no longer need the class and tell the VM to pop it off
the stack.
-->
这意味着执行每条 `OP_METHOD` 时，栈顶是方法的闭包，正下方是类。方法全部结束后，我们不再需要类，就让虚拟机把它弹出栈。

^code pop-class (1 before, 1 after)

<!--
Putting all of that together, here is an example class declaration to throw at
the compiler:
-->
把这一切拼起来，下面是扔给编译器的示例类声明：

```lox
class Brunch {
  bacon() {}
  eggs() {}
}
```

<!--
Given that, here is what the compiler generates and how those instructions
affect the stack at runtime:
-->
据此，编译器生成的指令，以及它们在运行时如何影响栈，如下：

<img src="image/methods-and-initializers/method-instructions.png" alt="The series of bytecode instructions for a class declaration with two methods." />

<!--
All that remains for us is to implement the runtime for that new `OP_METHOD`
instruction.
-->
剩下的，就是为这条新的 `OP_METHOD` 实现运行时了。

<!--
-- Executing method declarations
-->
### 执行方法声明

<!--
First we define the opcode.
-->
先定义操作码。

^code method-op (1 before, 1 after)

<!--
We disassemble it like other instructions that have string constant operands.
-->
反汇编方式和带有字符串常量操作数的其他指令一样。

^code disassemble-method (2 before, 1 after)

<!--
And over in the interpreter, we add a new case too.
-->
解释器那边也加一个新分支。

^code interpret-method (1 before, 1 after)

<!--
There, we read the method name from the constant table and pass it here:
-->
在那儿，我们从常量表读出方法名，再传到这里：

^code define-method

<!--
The method closure is on top of the stack, above the class it will be bound to.
We read those two stack slots and store the closure in the class's method table.
Then we pop the closure since we're done with it.
-->
方法闭包在栈顶，下方是它将绑定到的类。我们读这两个栈槽，把闭包存进类的方法表。用完后弹出闭包。

<!--
Note that we don't do any runtime type checking on the closure or class object.
That `AS_CLASS()` call is safe because the compiler itself generated the code
that causes the class to be in that stack slot. The VM <span
name="verify">trusts</span> its own compiler.
-->
注意：我们对闭包或类对象不做任何运行时类型检查。那次 `AS_CLASS()` 是安全的，因为正是编译器自己生成了让类出现在该栈槽的代码。虚拟机<span
name="verify">信任</span>自己的编译器。

<aside name="verify">

<!--
The VM trusts that the instructions it executes are valid because the *only* way
to get code to the bytecode interpreter is by going through clox's own compiler.
Many bytecode VMs, like the JVM and CPython, support executing bytecode that has
been compiled separately. That leads to a different security story. Maliciously
crafted bytecode could crash the VM or worse.

To prevent that, the JVM does a bytecode verification pass before it executes
any loaded code. CPython says it's up to the user to ensure any bytecode they
run is safe.
-->
虚拟机信任所执行指令的合法性，因为把代码送进字节码解释器的*唯一*途径，是经过 clox 自己的编译器。许多字节码虚拟机——如 JVM 与 CPython——支持执行另行编译的字节码。那会带来另一套安全叙事。恶意构造的字节码可能让虚拟机崩溃，或更糟。

为防此事，JVM 在执行任何已加载代码前会做一遍字节码校验。CPython 则说：确保所跑字节码安全，是用户自己的事。

</aside>

<!--
After the series of `OP_METHOD` instructions is done and the `OP_POP` has popped
the class, we will have a class with a nicely populated method table, ready to
start doing things. The next step is pulling those methods back out and using
them.
-->
一串 `OP_METHOD` 跑完、`OP_POP` 弹出类之后，我们就有了一个方法表填得妥妥的类，可以开始干活了。下一步是把那些方法再取出来用。

<!--
-- Method References
-->
## 方法引用

<!--
Most of the time, methods are accessed and immediately called, leading to this
familiar syntax:
-->
多数时候，方法被访问后立刻调用，于是有了这熟悉语法：

```lox
instance.method(argument);
```

<!--
But remember, in Lox and some other languages, those two steps are distinct and
can be separated.
-->
但请记住：在 Lox 以及另一些语言里，这两步是分开的，可以拆开。

```lox
var closure = instance.method;
closure(argument);
```

<!--
Since users *can* separate the operations, we have to implement them separately.
The first step is using our existing dotted property syntax to access a method
defined on the instance's class. That should return some kind of object that the
user can then call like a function.
-->
既然用户*可以*拆开操作，我们就必须分开实现。第一步：用已有的点号属性语法，访问定义在实例所属类上的方法。那应当返回某种对象，用户可以再像函数一样调用它。

<!--
The obvious approach is to look up the method in the class's method table and
return the ObjClosure associated with that name. But we also need to remember
that when you access a method, `this` gets bound to the instance the method was
accessed from. Here's the example from [when we added methods to jlox][jlox]:
-->
显而易见的做法是：在类的方法表里查找方法，返回与该名字关联的 ObjClosure。但还得记住：访问方法时，`this` 会绑定到取出方法的那个实例。下面是[我们给 jlox 加方法时][jlox]的例子：

[jlox]: classes.html#methods-on-classes

```lox
class Person {
  sayName() {
    print this.name;
  }
}

var jane = Person();
jane.name = "Jane";

var method = jane.sayName;
method(); // ?
```

<!--
This should print "Jane", so the object returned by `.sayName` somehow needs to
remember the instance it was accessed from when it later gets called. In jlox,
we implemented that "memory" using the interpreter's existing heap-allocated
Environment class, which handled all variable storage.
-->
这应当打印 `"Jane"`，所以 `.sayName` 返回的对象总得记得：稍后被调用时，它是从哪个实例上取下来的。在 jlox 里，我们用解释器已有的、堆上分配的 Environment 类实现这“记忆”——它负责全部变量存储。

<!--
Our bytecode VM has a more complex architecture for storing state. [Local
variables and temporaries][locals] are on the stack, [globals][] are in a hash
table, and variables in closures use [upvalues][]. That necessitates a somewhat
more complex solution for tracking a method's receiver in clox, and a new
runtime type.
-->
我们的字节码虚拟机存储状态的架构更复杂。[局部变量与临时值][locals]在栈上，[全局变量][globals]在哈希表里，闭包里的变量用[上值][upvalues]。于是在 clox 里追踪方法的接收者，需要略更复杂的方案，以及一种新的运行时类型。

[locals]: local-variables.html#representing-local-variables
[globals]: global-variables.html#variable-declarations
[upvalues]: closures.html#upvalues

<!--
-- Bound methods
-->
### 绑定方法

<!--
When the user executes a method access, we'll find the closure for that method
and wrap it in a new <span name="bound">"bound method"</span> object that tracks
the instance that the method was accessed from. This bound object can be called
later like a function. When invoked, the VM will do some shenanigans to wire up
`this` to point to the receiver inside the method's body.
-->
用户执行方法访问时，我们找到该方法的闭包，再把它包进一个新的<span name="bound">“绑定方法”</span>对象，由它记住方法是从哪个实例上取下的。这个绑定对象稍后可以像函数一样被调用。真正调用时，虚拟机会耍一点花招，把方法体内的 `this` 接到接收者上。

<aside name="bound">

<!--
I took the name "bound method" from CPython. Python behaves similar to Lox here,
and I used its implementation for inspiration.
-->
“绑定方法”这个名字我借自 CPython。Python 在这里的行为与 Lox 相近，我也从它的实现里汲取灵感。

</aside>

<!--
Here's the new object type:
-->
新的对象类型如下：

^code obj-bound-method (2 before, 1 after)

<!--
It wraps the receiver and the method closure together. The receiver's type is
Value even though methods can be called only on ObjInstances. Since the VM
doesn't care what kind of receiver it has anyway, using Value means we don't
have to keep converting the pointer back to a Value when it gets passed to more
general functions.
-->
它把接收者与方法闭包包在一起。接收者的类型是 Value，尽管方法只能在 ObjInstance 上调用。反正虚拟机并不在乎接收者是哪种，用 Value 就不必在传给更通用函数时反复把指针转回 Value。

<!--
The new struct implies the usual boilerplate you're used to by now. A new case
in the object type enum:
-->
新结构体意味着你已经熟透的那套样板。对象类型枚举里加一项：

^code obj-type-bound-method (1 before, 1 after)

<!--
A macro to check a value's type:
-->
检查值类型的宏：

^code is-bound-method (2 before, 1 after)

<!--
Another macro to cast the value to an ObjBoundMethod pointer:
-->
再一个宏，把值转成 ObjBoundMethod 指针：

^code as-bound-method (2 before, 1 after)

<!--
A function to create a new ObjBoundMethod:
-->
创建新 ObjBoundMethod 的函数：

^code new-bound-method-h (2 before, 1 after)

<!--
And an implementation of that function here:
-->
实现在这边：

^code new-bound-method

<!--
The constructor-like function simply stores the given closure and receiver. When
the bound method is no longer needed, we free it.
-->
这个构造函数式的函数只是存下给定的闭包与接收者。绑定方法不再需要时，我们释放它。

^code free-bound-method (1 before, 1 after)

<!--
The bound method has a couple of references, but it doesn't *own* them, so it
frees nothing but itself. However, those references do get traced by the garbage
collector.
-->
绑定方法持有几处引用，但并不*拥有*它们，所以除了自己什么也不释放。不过这些引用仍由垃圾回收器追踪。

^code blacken-bound-method (1 before, 1 after)

<!--
This <span name="trace">ensures</span> that a handle to a method keeps the
receiver around in memory so that `this` can still find the object when you
invoke the handle later. We also trace the method closure.
-->
这<span name="trace">保证</span>：握着方法句柄时，接收者仍留在内存里，好让你稍后调用句柄时 `this` 仍能找到那个对象。我们也追踪方法闭包。

<aside name="trace">

<!--
Tracing the method closure isn't really necessary. The receiver is an
ObjInstance, which has a pointer to its ObjClass, which has a table for all of
the methods. But it feels dubious to me in some vague way to have ObjBoundMethod
rely on that.
-->
其实不必追踪方法闭包。接收者是 ObjInstance，它有指向 ObjClass 的指针，类上又有全部方法的表。但让 ObjBoundMethod 依赖那条路径，总觉得有点含糊地不妥。

</aside>

<!--
The last operation all objects support is printing.
-->
所有对象都支持的最后一项操作是打印。

^code print-bound-method (1 before, 1 after)

<!--
A bound method prints exactly the same way as a function. From the user's
perspective, a bound method *is* a function. It's an object they can call. We
don't expose that the VM implements bound methods using a different object type.
-->
绑定方法的打印方式与函数完全相同。在用户看来，绑定方法*就是*函数——一个可调用的对象。我们不暴露虚拟机用另一种对象类型实现绑定方法这一点。

<aside name="party">

<img src="image/methods-and-initializers/party-hat.png" alt="A party hat." />

</aside>

<!--
Put on your <span name="party">party</span> hat because we just reached a little
milestone. ObjBoundMethod is the very last runtime type to add to clox. You've
written your last `IS_` and `AS_` macros. We're only a few chapters from the end
of the book, and we're getting close to a complete VM.
-->
戴上你的<span name="party">派对</span>帽吧——我们刚抵达一个小里程碑。ObjBoundMethod 是要给 clox 加的最后一个运行时类型。你已经写完了最后的 `IS_` 与 `AS_` 宏。离全书结尾只剩几章，一台完整的虚拟机近在咫尺。

<!--
-- Accessing methods
-->
### 访问方法

<!--
Let's get our new object type doing something. Methods are accessed using the
same "dot" property syntax we implemented in the last chapter. The compiler
already parses the right expressions and emits `OP_GET_PROPERTY` instructions
for them. The only changes we need to make are in the runtime.
-->
让新对象类型干点实事。方法通过上一章实现的同一套“点号”属性语法访问。编译器已经能解析正确表达式并发出 `OP_GET_PROPERTY`。我们只需改运行时。

<!--
When a property access instruction executes, the instance is on top of the
stack. The instruction's job is to find a field or method with the given name
and replace the top of the stack with the accessed property.
-->
属性访问指令执行时，实例在栈顶。指令的职责是：找到给定名字的字段或方法，并用所访问的属性替换栈顶。

<!--
The interpreter already handles fields, so we simply extend the
`OP_GET_PROPERTY` case with another section.
-->
解释器已能处理字段，我们只需给 `OP_GET_PROPERTY` 分支再加一段。

^code get-method (5 before, 1 after)

<!--
We insert this after the code to look up a field on the receiver instance.
Fields take priority over and shadow methods, so we look for a field first. If
the instance does not have a field with the given property name, then the name
may refer to a method.
-->
这段插在查找接收者实例上字段的代码之后。字段优先于方法并会遮蔽方法，所以先找字段。若实例没有该属性名的字段，名字才可能指向方法。

<!--
We take the instance's class and pass it to a new `bindMethod()` helper. If that
function finds a method, it places the method on the stack and returns `true`.
Otherwise it returns `false` to indicate a method with that name couldn't be
found. Since the name also wasn't a field, that means we have a runtime error,
which aborts the interpreter.
-->
我们取出实例的类，传给新的 `bindMethod()` 辅助函数。若找到方法，它把方法放到栈上并返回 `true`；否则返回 `false`，表示找不到该名方法。既然名字也不是字段，那就是运行时错误，中止解释器。

<!--
Here is the good stuff:
-->
好戏在这里：

^code bind-method

<!--
First we look for a method with the given name in the class's method table. If
we don't find one, we report a runtime error and bail out. Otherwise, we take
the method and wrap it in a new ObjBoundMethod. We grab the receiver from its
home on top of the stack. Finally, we pop the instance and replace the top of
the stack with the bound method.
-->
先在类的方法表里按名字找方法。找不到就报告运行时错误并退出。否则取出方法，包进新的 ObjBoundMethod。接收者就在栈顶自家位置，我们把它拿来。最后弹出实例，用绑定方法替换栈顶。

<!--
For example:
-->
例如：

```lox
class Brunch {
  eggs() {}
}

var brunch = Brunch();
var eggs = brunch.eggs;
```

<!--
Here is what happens when the VM executes the `bindMethod()` call for the
`brunch.eggs` expression:
-->
虚拟机为 `brunch.eggs` 表达式执行 `bindMethod()` 时，发生的事如下：

<img src="image/methods-and-initializers/bind-method.png" alt="The stack changes caused by bindMethod()." />

<!--
That's a lot of machinery under the hood, but from the user's perspective, they
simply get a function that they can call.
-->
引擎盖下机件不少，但在用户看来，他们只是拿到一个可以调用的函数。

<!--
-- Calling methods
-->
### 调用方法

<!--
Users can declare methods on classes, access them on instances, and get bound
methods onto the stack. They just can't <span name="do">*do*</span> anything
useful with those bound method objects. The operation we're missing is calling
them. Calls are implemented in `callValue()`, so we add a case there for the new
object type.
-->
用户可以在类上声明方法、在实例上访问它们，并把绑定方法弄到栈上。只是还不能拿这些绑定方法对象<span name="do">*做*</span>任何有用的事。缺的正是调用。调用在 `callValue()` 里实现，我们为新对象类型加一个分支。

<aside name="do">

<!--
A bound method *is* a first-class value, so they can store it in variables, pass
it to functions, and otherwise do "value"-y stuff with it.
-->
绑定方法*是*一等值，所以可以存进变量、传给函数，以及做其他“值”该做的事。

</aside>

^code call-bound-method (1 before, 1 after)

<!--
We pull the raw closure back out of the ObjBoundMethod and use the existing
`call()` helper to begin an invocation of that closure by pushing a CallFrame
for it onto the call stack. That's all it takes to be able to run this Lox
program:
-->
我们从 ObjBoundMethod 里取出原始闭包，用现成的 `call()` 辅助函数开始调用：往调用栈上压一个 CallFrame。这就足以跑下面这段 Lox 程序：

```lox
class Scone {
  topping(first, second) {
    print "scone with " + first + " and " + second;
  }
}

var scone = Scone();
scone.topping("berries", "cream");
```

<!--
That's three big steps. We can declare, access, and invoke methods. But
something is missing. We went to all that trouble to wrap the method closure in
an object that binds the receiver, but when we invoke the method, we don't use
that receiver at all.
-->
三大步完成了：可以声明、访问并调用方法。可还缺一样。我们费尽周折把方法闭包包进绑定接收者的对象，真正调用时却完全没用到那个接收者。

<!--
-- This
-->
## this

<!--
The reason bound methods need to keep hold of the receiver is so that it can be
accessed inside the body of the method. Lox exposes a method's receiver through
`this` expressions. It's time for some new syntax. The lexer already treats
`this` as a special token type, so the first step is wiring that token up in the
parse table.
-->
绑定方法之所以要紧握接收者，是为了能在方法体内部访问它。Lox 通过 `this` 表达式暴露方法的接收者。是时候加一点新语法了。词法分析器已把 `this` 当成特殊 token 类型，第一步是把它接到解析表上。

^code table-this (1 before, 1 after)

<aside name="this">

<!--
The underscore at the end of the name of the parser function is because `this`
is a reserved word in C++ and we support compiling clox as C++.
-->
解析函数名末尾的下划线，是因为 `this` 在 C++ 里是保留字，而我们支持把 clox 当 C++ 来编译。

</aside>

<!--
When the parser encounters a `this` in prefix position, it dispatches to a new
parser function.
-->
解析器在前缀位置遇到 `this` 时，会派发到一个新的解析函数。

^code this

<!--
We'll apply the same implementation technique for `this` in clox that we used in
jlox. We treat `this` as a lexically scoped local variable whose value gets
magically initialized. Compiling it like a local variable means we get a lot of
behavior for free. In particular, closures inside a method that reference `this`
will do the right thing and capture the receiver in an upvalue.
-->
clox 里对 `this` 采用与 jlox 相同的实现手法。我们把 `this` 当成一个词法作用域局部变量，其值被魔法般初始化。按局部变量来编译，许多行为就白捡了。尤其是：方法内引用 `this` 的闭包会做对的事，把接收者捕获进上值。

<!--
When the parser function is called, the `this` token has just been consumed and
is stored as the previous token. We call our existing `variable()` function
which compiles identifier expressions as variable accesses. It takes a single
Boolean parameter for whether the compiler should look for a following `=`
operator and parse a setter. You can't assign to `this`, so we pass `false` to
disallow that.
-->
解析函数被调用时，`this` token 刚被消费，存在 previous token 里。我们调用现成的 `variable()`，它把标识符表达式编译成变量访问。它接受一个布尔参数：编译器是否该寻找后面的 `=` 并解析成赋值。你不能给 `this` 赋值，所以传 `false` 禁止此事。

<!--
The `variable()` function doesn't care that `this` has its own token type and
isn't an identifier. It is happy to treat the lexeme "this" as if it were a
variable name and then look it up using the existing scope resolution machinery.
Right now, that lookup will fail because we never declared a variable whose name
is "this". It's time to think about where the receiver should live in memory.
-->
`variable()` 并不在乎 `this` 有自己的 token 类型、不是标识符。它乐意把词素 `"this"` 当成变量名，再用现有的作用域解析机制去查。眼下查找会失败，因为我们从未声明过名为 `"this"` 的变量。该想想接收者该住在内存何处了。

<!--
At least until they get captured by closures, clox stores every local variable
on the VM's stack. The compiler keeps track of which slots in the function's
stack window are owned by which local variables. If you recall, the compiler
sets aside stack slot zero by declaring a local variable whose name is an empty
string.
-->
至少在被闭包捕获之前，clox 把每个局部变量都放在虚拟机栈上。编译器跟踪函数栈窗口里哪些槽属于哪些局部变量。你若还记得：编译器通过声明一个名为空字符串的局部变量，预留了栈槽零。

<!--
For function calls, that slot ends up holding the function being called. Since
the slot has no name, the function body never accesses it. You can guess where
this is going. For *method* calls, we can repurpose that slot to store the
receiver. Slot zero will store the instance that `this` is bound to. In order to
compile `this` expressions, the compiler simply needs to give the correct name
to that local variable.
-->
对函数调用，那个槽最终放着被调用的函数。槽没有名字，函数体从不访问它。你大概猜到要往哪儿走了。对*方法*调用，我们可以把那个槽改作存放接收者。槽零将存放 `this` 所绑定的实例。要编译 `this` 表达式，编译器只需给那个局部变量起对名字。

^code slot-zero (1 before, 1 after)

<!--
We want to do this only for methods. Function declarations don't have a `this`.
And, in fact, they *must not* declare a variable named "this", so that if you
write a `this` expression inside a function declaration which is itself inside a
method, the `this` correctly resolves to the outer method's receiver.
-->
我们只想对方法这么做。函数声明没有 `this`。而且它们*绝不能*声明名为 `"this"` 的变量，这样：若你在方法内部的函数声明里写 `this` 表达式，`this` 才会正确解析到外层方法的接收者。

```lox
class Nested {
  method() {
    fun function() {
      print this;
    }

    function();
  }
}

Nested().method();
```

<!--
This program should print "Nested instance". To decide what name to give to
local slot zero, the compiler needs to know whether it's compiling a function or
method declaration, so we add a new case to our FunctionType enum to distinguish
methods.
-->
这段程序应当打印 `"Nested instance"`。要决定给局部槽零起什么名字，编译器得知道自己在编译函数还是方法声明，于是我们在 FunctionType 枚举里加一项来区分方法。

^code method-type-enum (1 before, 1 after)

<!--
When we compile a method, we use that type.
-->
编译方法时，我们使用那个类型。

^code method-type (2 before, 1 after)

<!--
Now we can correctly compile references to the special "this" variable, and the
compiler will emit the right `OP_GET_LOCAL` instructions to access it. Closures
can even capture `this` and store the receiver in upvalues. Pretty cool.
-->
现在我们可以正确编译对特殊变量 `"this"` 的引用，编译器会发出正确的 `OP_GET_LOCAL` 来访问它。闭包甚至可以捕获 `this`，把接收者存进上值。挺酷。

<!--
Except that at runtime, the receiver isn't actually *in* slot zero. The
interpreter isn't holding up its end of the bargain yet. Here is the fix:
-->
只不过在运行时，接收者其实并不*在*槽零里。解释器还没履行它那头的约定。修补如下：

^code store-receiver (2 before, 2 after)

<!--
When a method is called, the top of the stack contains all of the arguments, and
then just under those is the closure of the called method. That's where slot
zero in the new CallFrame will be. This line of code inserts the receiver into
that slot. For example, given a method call like this:
-->
方法被调用时，栈顶是全部参数，再往下是被调方法的闭包。那正是新 CallFrame 里槽零所在。这行代码把接收者插入那个槽。例如，给定这样的方法调用：

```lox
scone.topping("berries", "cream");
```

<!--
We calculate the slot to store the receiver like so:
-->
我们这样计算存放接收者的槽：

<img src="image/methods-and-initializers/closure-slot.png" alt="Skipping over the argument stack slots to find the slot containing the closure." />

<!--
The `-argCount` skips past the arguments and the `- 1` adjusts for the fact that
`stackTop` points just *past* the last used stack slot.
-->
`-argCount` 跳过参数，`- 1` 则是因为 `stackTop` 指向最后一个已用栈槽的*再往前一格*。

<!--
-- Misusing this
-->
### 误用 this

<!--
Our VM now supports users *correctly* using `this`, but we also need to make
sure it properly handles users *mis*using `this`. Lox says it is a compile
error for a `this` expression to appear outside of the body of a method. These
two wrong uses should be caught by the compiler:
-->
虚拟机现在支持用户*正确*使用 `this`，但我们也得确保它妥善处理用户*误*用 `this`。Lox 规定：`this` 表达式出现在方法体之外是编译错误。下面两种错误用法应由编译器抓住：

```lox
print this; // At top level.

fun notMethod() {
  print this; // In a function.
}
```

<!--
So how does the compiler know if it's inside a method? The obvious answer is to
look at the FunctionType of the current Compiler. We did just add an enum case
there to treat methods specially. However, that wouldn't correctly handle code
like the earlier example where you are inside a function which is, itself,
nested inside a method.
-->
那编译器怎么知道自己是否在方法里？显而易见的答案是看当前 Compiler 的 FunctionType。我们刚加了一个枚举项来特殊对待方法。不过那无法正确处理前面那种情况：你在一个函数里，而该函数本身又嵌在方法里。

<!--
We could try to resolve "this" and then report an error if it wasn't found in
any of the surrounding lexical scopes. That would work, but would require us to
shuffle around a bunch of code, since right now the code for resolving a
variable implicitly considers it a global access if no declaration is found.
-->
我们可以尝试解析 `"this"`，若周围任何词法作用域都找不到就报错。那样能行，但要挪动不少代码：眼下解析变量时，找不到声明就会隐式当成全局访问。

<!--
In the next chapter, we will need information about the nearest enclosing class.
If we had that, we could use it here to determine if we are inside a method. So
we may as well make our future selves' lives a little easier and put that
machinery in place now.
-->
下一章我们会需要最近包围类的信息。若手里有它，这里就能用来判断是否在方法内。不如让未来的自己轻松一点，现在就把这套机制装上。

^code current-class (1 before, 2 after)

<!--
This module variable points to a struct representing the current, innermost
class being compiled. The new type looks like this:
-->
这个模块变量指向表示当前、最内层正在编译的类的结构体。新类型长这样：

^code class-compiler-struct (1 before, 2 after)

<!--
Right now we store only a pointer to the ClassCompiler for the enclosing class,
if any. Nesting a class declaration inside a method in some other class is an
uncommon thing to do, but Lox supports it. Just like the Compiler struct, this
means ClassCompiler forms a linked list from the current innermost class being
compiled out through all of the enclosing classes.
-->
眼下我们只存一个指向包围类（若有）的 ClassCompiler 的指针。在某个类的方法里再嵌套声明另一个类并不常见，但 Lox 支持。和 Compiler 结构体一样，这意味着 ClassCompiler 形成一条链表：从当前最内层正在编译的类，一路穿出所有包围类。

<!--
If we aren't inside any class declaration at all, the module variable
`currentClass` is `NULL`. When the compiler begins compiling a class, it pushes
a new ClassCompiler onto that implict linked stack.
-->
若根本不在任何类声明里，模块变量 `currentClass` 为 `NULL`。编译器开始编译一个类时，就把一个新的 ClassCompiler 压上那条隐式链接栈。

^code create-class-compiler (2 before, 1 after)

<!--
The memory for the ClassCompiler struct lives right on the C stack, a handy
capability we get by writing our compiler using recursive descent. At the end of
the class body, we pop that compiler off the stack and restore the enclosing
one.
-->
ClassCompiler 结构体的内存就住在 C 栈上——用递归下降写编译器带来的便利。类体结束时，我们把那个编译器弹出栈，恢复包围的那个。

^code pop-enclosing (1 before, 1 after)

<!--
When an outermost class body ends, `enclosing` will be `NULL`, so this resets
`currentClass` to `NULL`. Thus, to see if we are inside a class -- and therefore
inside a method -- we simply check that module variable.
-->
最外层类体结束时，`enclosing` 为 `NULL`，于是把 `currentClass` 重置为 `NULL`。因此，要看我们是否在类里——从而是否在方法里——只需检查那个模块变量。

^code this-outside-class (1 before, 1 after)

<!--
With that, `this` outside of a class is correctly forbidden. Now our methods
really feel like *methods* in the object-oriented sense. Accessing the receiver
lets them affect the instance you called the method on. We're getting there!
-->
如此，类外的 `this` 就被正确禁止了。如今我们的方法，才真正有面向对象意义上*方法*的感觉。访问接收者，让它们能影响你调用方法所在的那个实例。我们正一步步靠近！

<!--
-- Instance Initializers
-->
## 实例初始化器

<!--
The reason object-oriented languages tie state and behavior together -- one of
the core tenets of the paradigm -- is to ensure that objects are always in a
valid, meaningful state. When the only way to touch an object's state is <span
name="through">through</span> its methods, the methods can make sure nothing
goes awry. But that presumes the object is *already* in a proper state. What
about when it's first created?
-->
面向对象语言把状态与行为绑在一起——范式的核心信条之一——是为了确保对象始终处于有效、有意义的状态。若触碰对象状态的唯一途径是<span
name="through">经由</span>其方法，方法就能确保不出岔子。但那假定对象*已经*处于妥当状态。那它刚被创建时呢？

<aside name="through">

<!--
Of course, Lox does let outside code directly access and modify an instance's
fields without going through its methods. This is unlike Ruby and Smalltalk,
which completely encapsulate state inside objects. Our toy scripting language,
alas, isn't so principled.
-->
当然，Lox 确实允许外部代码不经方法、直接访问并修改实例字段。这与 Ruby 和 Smalltalk 不同——它们把状态完全封装在对象内。我们的玩具脚本语言，唉，没那么讲原则。

</aside>

<!--
Object-oriented languages ensure that brand new objects are properly set up
through constructors, which both produce a new instance and initialize its
state. In Lox, the runtime allocates new raw instances, and a class may declare
an initializer to set up any fields. Initializers work mostly like normal
methods, with a few tweaks:
-->
面向对象语言通过构造函数确保崭新对象被妥当设置：既生产新实例，又初始化其状态。在 Lox 里，运行时分配生的新实例，类可以声明一个初始化器来设置字段。初始化器大体像普通方法，只是有几处微调：

<!--
1.  The runtime automatically invokes the initializer method whenever an
    instance of a class is created.

2.  The caller that constructs an instance always gets the instance <span
    name="return">back</span> after the initializer finishes, regardless of what
    the initializer function itself returns. The initializer method doesn't need
    to explicitly return `this`.

3.  In fact, an initializer is *prohibited* from returning any value at all
    since the value would never be seen anyway.
-->
1.  每当创建类的实例时，运行时自动调用初始化器方法。

2.  构造实例的调用者在初始化器结束后总是拿<span
    name="return">回</span>该实例，无论初始化器函数本身返回什么。初始化器不必显式 `return this`。

3.  事实上，初始化器被*禁止*返回任何值，因为那值反正也看不见。

<aside name="return">

<!--
It's as if the initializer is implicitly wrapped in a bundle of code like this:

```lox
fun create(klass) {
  var obj = newInstance(klass);
  obj.init();
  return obj;
}
```

Note how the value returned by `init()` is discarded.
-->
就好像初始化器被隐式包进这样一捆代码：

```lox
fun create(klass) {
  var obj = newInstance(klass);
  obj.init();
  return obj;
}
```

注意：`init()` 的返回值被丢弃了。

</aside>

<!--
Now that we support methods, to add initializers, we merely need to implement
those three special rules. We'll go in order.
-->
既然已支持方法，要加初始化器，只需实现这三条特殊规则。我们按顺序来。

<!--
-- Invoking initializers
-->
### 调用初始化器

<!--
First, automatically calling `init()` on new instances:
-->
首先，在新实例上自动调用 `init()`：

^code call-init (1 before, 1 after)

<!--
After the runtime allocates the new instance, we look for an `init()` method on
the class. If we find one, we initiate a call to it. This pushes a new CallFrame
for the initializer's closure. Say we run this program:
-->
运行时分配新实例后，我们在类上查找 `init()` 方法。若找到，就发起对它的调用。这会为初始化器的闭包压上一个新 CallFrame。假设跑这段程序：

```lox
class Brunch {
  init(food, drink) {}
}

Brunch("eggs", "coffee");
```

<!--
When the VM executes the call to `Brunch()`, it goes like this:
-->
虚拟机执行对 `Brunch()` 的调用时，情形如下：

<img src="image/methods-and-initializers/init-call-frame.png" alt="The aligned stack windows for the Brunch() call and the corresponding init() method it forwards to." />

<!--
Any arguments passed to the class when we called it are still sitting on the
stack above the instance. The new CallFrame for the `init()` method shares that
stack window, so those arguments implictly get forwarded to the initializer.
-->
调用类时传入的任何参数仍坐在实例上方的栈上。`init()` 方法的新 CallFrame 共享那扇栈窗口，于是那些参数被隐式转发给初始化器。

<!--
Lox doesn't require a class to define an initializer. If omitted, the runtime
simply returns the new uninitialized instance. However, if there is no `init()`
method, then it doesn't make any sense to pass arguments to the class when
creating the instance. We make that an error.
-->
Lox 不要求类必须定义初始化器。若省略，运行时直接返回未初始化的新实例。可是若没有 `init()` 方法，创建实例时再给类传参就毫无意义。我们把这定为错误。

^code no-init-arity-error (1 before, 1 after)

<!--
When the class *does* provide an initializer, we also need to ensure that the
number of arguments passed matches the initializer's arity. Fortunately, the
`call()` helper does that for us already.
-->
当类*确实*提供初始化器时，我们还得确保传入参数个数与初始化器的元数匹配。幸好 `call()` 辅助函数已经替我们做了。

<!--
To call the initializer, the runtime looks up the `init()` method by name. We
want that to be fast since it happens every time an instance is constructed.
That means it would be good to take advantage of the string interning we've
already implemented. To do that, the VM creates an ObjString for "init" and
reuses it. The string lives right in the VM struct.
-->
要调用初始化器，运行时按名字查找 `init()`。我们希望这很快，因为每次构造实例都会发生。那就该好好利用已实现的字符串驻留。为此，虚拟机为 `"init"` 创建一个 ObjString 并复用它。字符串就住在 VM 结构体里。

^code vm-init-string (1 before, 1 after)

<!--
We create and intern the string when the VM boots up.
-->
虚拟机启动时创建并驻留该字符串。

^code init-init-string (1 before, 2 after)

<!--
We want it to stick around, so the GC considers it a root.
-->
我们希望它一直留下，所以 GC 把它当作根。

^code mark-init-string (1 before, 1 after)

<!--
Look carefully. See any bug waiting to happen? No? It's a subtle one. The
garbage collector now reads `vm.initString`. That field is initialized from the
result of calling `copyString()`. But copying a string allocates memory, which
can trigger a GC. If the collector ran at just the wrong time, it would read
`vm.initString` before it had been initialized. So, first we zero the field out.
-->
仔细看。看出潜伏的缺陷了吗？没有？这是个微妙的。垃圾回收器现在会读 `vm.initString`。该字段由调用 `copyString()` 的结果初始化。但复制字符串会分配内存，可能触发 GC。若收集器恰在错误时刻跑，就会在字段初始化之前读到 `vm.initString`。所以，我们先把字段清零。

^code null-init-string (2 before, 2 after)

<!--
We clear the pointer when the VM shuts down since the next line will free it.
-->
虚拟机关闭时清掉指针，因为下一行会释放它。

^code clear-init-string (1 before, 1 after)

<!--
OK, that lets us call initializers.
-->
好，这样我们就能调用初始化器了。

<!--
-- Initializer return values
-->
### 初始化器的返回值

<!--
The next step is ensuring that constructing an instance of a class with an
initializer always returns the new instance, and not `nil` or whatever the body
of the initializer returns. Right now, if a class defines an initializer, then
when an instance is constructed, the VM pushes a call to that initializer onto
the CallFrame stack. Then it just keeps on trucking.
-->
下一步是确保：构造带初始化器的类的实例时，总是返回新实例，而不是 `nil` 或初始化器体返回的随便什么。眼下若类定义了初始化器，构造实例时虚拟机会把对该初始化器的调用压上 CallFrame 栈，然后继续埋头往前开。

<!--
The user's invocation on the class to create the instance will complete whenever
that initializer method returns, and will leave on the stack whatever value the
initializer puts there. That means that unless the user takes care to put
`return this;` at the end of the initializer, no instance will come out. Not
very helpful.
-->
用户为创建实例而对类的调用，会在初始化器方法返回时完成，并把初始化器放在栈上的值留下。这意味着：除非用户记得在初始化器末尾写 `return this;`，否则拿不到实例。不太好用。

<!--
To fix this, whenever the front end compiles an initializer method, it will emit
different bytecode at the end of the body to return `this` from the method
instead of the usual implicit `nil` most functions return. In order to do
*that*, the compiler needs to actually know when it is compiling an initializer.
We detect that by checking to see if the name of the method we're compiling is
"init".
-->
为修好这一点：前端编译初始化器方法时，会在方法体末尾发出不同的字节码，让方法返回 `this`，而不是多数函数那种隐式 `nil`。要做*到*这一点，编译器得真正知道自己何时在编译初始化器。我们通过检查正在编译的方法名是否为 `"init"` 来检测。

^code initializer-name (1 before, 1 after)

<!--
We define a new function type to distinguish initializers from other methods.
-->
我们定义一种新的函数类型，把初始化器与其他方法区分开。

^code initializer-type-enum (1 before, 1 after)

<!--
Whenever the compiler emits the implicit return at the end of a body, we check
the type to decide whether to insert the initializer-specific behavior.
-->
每当编译器在方法体末尾发出隐式 return 时，我们检查类型，决定是否插入初始化器特有的行为。

^code return-this (1 before, 1 after)

<!--
In an initializer, instead of pushing `nil` onto the stack before returning,
we load slot zero, which contains the instance. This `emitReturn()` function is
also called when compiling a `return` statement without a value, so this also
correctly handles cases where the user does an early return inside the
initializer.
-->
在初始化器里，返回前不是把 `nil` 压栈，而是加载槽零——那里装着实例。编译无值的 `return` 语句时也会调用这个 `emitReturn()`，因此用户在初始化器里提前 return 的情况也被正确处理。

<!--
-- Incorrect returns in initializers
-->
### 初始化器中错误的 return

<!--
The last step, the last item in our list of special features of initializers, is
making it an error to try to return anything *else* from an initializer. Now
that the compiler tracks the method type, this is straightforward.
-->
最后一步，也是初始化器特殊特性清单上的最后一项：试图从初始化器返回任何*别的*东西，都定为错误。既然编译器已跟踪方法类型，这很直截了当。

^code return-from-init (3 before, 1 after)

<!--
We report an error if a `return` statement in an initializer has a value. We
still go ahead and compile the value afterwards so that the compiler doesn't get
confused by the trailing expression and report a bunch of cascaded errors.
-->
若初始化器里的 `return` 语句带有值，我们就报错。之后仍继续编译那个值，以免编译器被尾随表达式搞糊涂，连带报出一串级联错误。

<!--
Aside from inheritance, which we'll get to [soon][super], we now have a
fairly full-featured class system working in clox.
-->
除了继承——我们[很快][super]会讲到——如今 clox 里已有一套相当完整的类系统在运转。

```lox
class CoffeeMaker {
  init(coffee) {
    this.coffee = coffee;
  }

  brew() {
    print "Enjoy your cup of " + this.coffee;

    // No reusing the grounds!
    this.coffee = nil;
  }
}

var maker = CoffeeMaker("coffee and chicory");
maker.brew();
```

<!--
Pretty fancy for a C program that would fit on an old <span
name="floppy">floppy</span> disk.
-->
对一个能塞进老式<span
name="floppy">软盘</span>的 C 程序来说，相当花哨了。

<aside name="floppy">

<!--
I acknowledge that "floppy disk" may no longer be a useful size reference for
current generations of programmers. Maybe I should have said "a few tweets" or
something.
-->
我承认，“软盘”对当今这代程序员或许已不再是有用的体量参照。或许我该说“几条推文”之类。

</aside>

<!--
-- Optimized Invocations
-->
## 优化的调用

<!--
Our VM correctly implements the language's semantics for method calls and
initializers. We could stop here. But the main reason we are building an entire
second implementation of Lox from scratch is to execute faster than our old Java
interpreter. Right now, method calls even in clox are slow.
-->
我们的虚拟机正确实现了方法调用与初始化器的语言语义。可以停在这里。可我们从零重做整套第二份 Lox 实现的主因，是要比旧的 Java 解释器跑得更快。眼下即便在 clox 里，方法调用也慢。

<!--
Lox's semantics define a method invocation as two operations -- accessing the
method and then calling the result. Our VM must support those as separate
operations because the user *can* separate them. You can access a method without
calling it and then invoke the bound method later. Nothing we've implemented so
far is unnecessary.
-->
Lox 的语义把方法调用定义为两步操作——访问方法，再调用结果。虚拟机必须支持把它们当分开的操作，因为用户*可以*拆开：你可以访问方法而不调用，稍后再调用绑定方法。目前实现的东西没有多余。

<!--
But *always* executing those as separate operations has a significant cost.
Every single time a Lox program accesses and invokes a method, the runtime
heap allocates a new ObjBoundMethod, initializes its fields, then pulls them
right back out. Later, the GC has to spend time freeing all of those ephemeral
bound methods.
-->
但*总是*当成分开的操作执行，代价不小。Lox 程序每次访问并调用方法，运行时都在堆上分配一个新的 ObjBoundMethod，初始化字段，再立刻把它们抽出来。随后 GC 还得花时间释放所有这些短命的绑定方法。

<!--
Most of the time, a Lox program accesses a method and then immediately calls it.
The bound method is created by one bytecode instruction and then consumed by the
very next one. In fact, it's so immediate that the compiler can even textually
*see* that it's happening -- a dotted property access followed by an opening
parenthesis is most likely a method call.
-->
多数时候，Lox 程序访问方法后立刻调用。绑定方法由一条字节码指令创建，紧接着就被下一条消费。事实上快到编译器甚至能从文本上*看见*——点号属性访问后面跟着左括号，多半就是方法调用。

<!--
Since we can recognize this pair of operations at compile time, we have the
opportunity to emit a <span name="super">new, special</span> instruction that
performs an optimized method call.
-->
既然能在编译期认出这对操作，我们就有机会发出一条<span name="super">新的、特殊的</span>指令，执行优化过的方法调用。

<!--
We start in the function that compiles dotted property expressions.
-->
我们从编译点号属性表达式的函数入手。

<aside name="super" class="bottom">

<!--
If you spend enough time watching your bytecode VM run, you'll notice it often
executes the same series of bytecode instructions one after the other. A classic
optimization technique is to define a new single instruction called a
**superinstruction** that fuses those into a single instruction with the same
behavior as the entire sequence.

One of the largest performance drains in a bytecode interpreter is the overhead
of decoding and dispatching each instruction. Fusing several instructions into
one eliminates some of that.

The challenge is determining *which* instruction sequences are common enough to
benefit from this optimization. Every new superinstruction claims an opcode for
its own use and there are only so many of those to go around. Add too many, and
you'll need a larger encoding for opcodes, which then increases code size and
makes decoding *all* instructions slower.
-->
若你花够时间盯着字节码虚拟机跑，会发现它常常接连执行同一串字节码指令。经典优化手法是：定义一条叫作**超指令**（superinstruction）的新单指令，把那串融成一条、行为与整段序列相同的指令。

字节码解释器最大的性能开销之一，是每条指令的解码与分派。把几条融成一条，就能消掉一部分。

难处在于判定*哪些*指令序列常见到值得优化。每条新超指令都要占一个操作码，而操作码数量有限。加太多，就需要更大的操作码编码，从而增大代码体积，并让*所有*指令的解码变慢。

</aside>

^code parse-call (3 before, 1 after)

<!--
After the compiler has parsed the property name, we look for a left parenthesis.
If we match one, we switch to a new code path. There, we compile the argument
list exactly like we do when compiling a call expression. Then we emit a single
new `OP_INVOKE` instruction. It takes two operands:
-->
编译器解析完属性名后，我们寻找左括号。若匹配到，就切到新代码路径。在那儿，我们像编译调用表达式一样编译参数列表，然后发出单条新的 `OP_INVOKE`。它有两个操作数：

<!--
1.  The index of the property name in the constant table.

2.  The number of arguments passed to the method.
-->
1.  属性名在常量表中的索引。

2.  传给方法的参数个数。

<!--
In other words, this single instruction combines the operands of the
`OP_GET_PROPERTY` and `OP_CALL` instructions it replaces, in that order. It
really is a fusion of those two instructions. Let's define it.
-->
换言之，这条单指令按顺序合并了它所取代的 `OP_GET_PROPERTY` 与 `OP_CALL` 的操作数。它真的是那两条指令的融合。来定义它。

^code invoke-op (1 before, 1 after)

<!--
And add it to the disassembler:
-->
并加进反汇编器：

^code disassemble-invoke (2 before, 1 after)

<!--
This is a new, special instruction format, so it needs a little custom
disassembly logic.
-->
这是新的特殊指令格式，需要一点定制反汇编逻辑。

^code invoke-instruction

<!--
We read the two operands and then print out both the method name and the
argument count. Over in the interpreter's bytecode dispatch loop is where the
real action begins.
-->
我们读两个操作数，再打印方法名与参数个数。真正的好戏在解释器的字节码分派循环里开始。

^code interpret-invoke (1 before, 1 after)

<!--
Most of the work happens in `invoke()`, which we'll get to. Here, we look up the
method name from the first operand and then read the argument count operand.
Then we hand off to `invoke()` to do the heavy lifting. That function returns
`true` if the invocation succeeds. As usual, a `false` return means a runtime
error occurred. We check for that here and abort the interpreter if disaster has
struck.
-->
大部分工作发生在 `invoke()` 里，稍后再讲。这里我们从第一个操作数查方法名，再读参数个数操作数，然后交给 `invoke()` 干重活。调用成功则返回 `true`。照例，返回 `false` 表示发生了运行时错误。我们在此检查，若灾难降临就中止解释器。

<!--
Finally, assuming the invocation succeeded, then there is a new CallFrame on the
stack, so we refresh our cached copy of the current frame in `frame`.
-->
最后，假定调用成功，栈上就有了新的 CallFrame，于是我们刷新缓存在 `frame` 里的当前帧副本。

<!--
The interesting work happens here:
-->
有意思的活在这里：

^code invoke

<!--
First we grab the receiver off the stack. The arguments passed to the method are
above it on the stack, so we peek that many slots down. Then it's a simple
matter to cast the object to an instance and invoke the method on it.
-->
先从栈上抓出接收者。传给方法的参数在它上方，所以我们向下窥视那么多槽。然后把对象转成实例并在其上调用方法，就很简单了。

<!--
That does assume the object *is* an instance. As with `OP_GET_PROPERTY`
instructions, we also need to handle the case where a user incorrectly tries to
call a method on a value of the wrong type.
-->
那假定对象*是*实例。和 `OP_GET_PROPERTY` 一样，我们也得处理用户错误地试图在错误类型的值上调用方法的情况。

^code invoke-check-type (1 before, 1 after)

<!--
<span name="helper">That's</span> a runtime error, so we report that and bail
out. Otherwise, we get the instance's class and jump over to this other new
utility function:
-->
<span name="helper">那</span>是运行时错误，于是报告并退出。否则取出实例的类，跳到另一个新的工具函数：

<aside name="helper">

<!--
As you can guess by now, we split this code into a separate function because
we're going to reuse it later -- in this case for `super` calls.
-->
你大概猜到了：我们把这段拆成单独函数，是因为稍后还要复用——这里是为了 `super` 调用。

</aside>

^code invoke-from-class

<!--
This function combines the logic of how the VM implements `OP_GET_PROPERTY` and
`OP_CALL` instructions, in that order. First we look up the method by name in
the class's method table. If we don't find one, we report that runtime error and
exit.
-->
这个函数按顺序合并了虚拟机实现 `OP_GET_PROPERTY` 与 `OP_CALL` 的逻辑。先在类的方法表里按名查找方法。找不到就报告运行时错误并退出。

<!--
Otherwise, we take the method's closure and push a call to it onto the CallFrame
stack. We don't need to heap allocate and initialize an ObjBoundMethod. In fact,
we don't even need to <span name="juggle">juggle</span> anything on the stack.
The receiver and method arguments are already right where they need to be.
-->
否则取出方法的闭包，把对它的调用压上 CallFrame 栈。我们不必在堆上分配并初始化 ObjBoundMethod。事实上，甚至不必在栈上<span name="juggle">腾挪</span>任何东西。接收者与方法参数已经各就各位。

<aside name="juggle">

<!--
This is a key reason *why* we use stack slot zero to store the receiver -- it's
how the caller already organizes the stack for a method call. An efficient
calling convention is an important part of a bytecode VM's performance story.
-->
这正是我们用栈槽零存放接收者的关键原因——调用者组织方法调用栈的方式本来就是这样。高效的调用约定，是字节码虚拟机性能故事的重要一章。

</aside>

<!--
If you fire up the VM and run a little program that calls methods now, you
should see the exact same behavior as before. But, if we did our job right, the
*performance* should be much improved. I wrote a little microbenchmark that
does a batch of 10,000 method calls. Then it tests how many of these batches it
can execute in 10 seconds. On my computer, without the new `OP_INVOKE`
instruction, it got through 1,089 batches. With this new optimization, it
finished 8,324 batches in the same time. That's *7.6 times faster*, which is a
huge improvement when it comes to programming language optimization.
-->
现在启动虚拟机，跑一个会调用方法的小程序，行为应与从前一模一样。但若我们干得漂亮，*性能*应大有改善。我写了一个小微基准：每批做 10,000 次方法调用，再测 10 秒内能跑多少批。在我的电脑上，没有新的 `OP_INVOKE` 时跑完 1,089 批；加上这项优化，同样时间内完成 8,324 批。那是*快 7.6 倍*——对编程语言优化而言，是巨大改进。

<aside name="pat">

<!--
We shouldn't pat ourselves on the back *too* firmly. This performance
improvement is relative to our own unoptimized method call implementation which
was quite slow. Doing a heap allocation for every single method call isn't going
to win any races.
-->
我们不该*太*用力地<span name="pat">拍</span>自己的背。这份性能提升是相对于我们自己未优化的、相当慢的方法调用实现而言的。每次方法调用都做一次堆分配，可赢不了任何比赛。

</aside>

<img src="image/methods-and-initializers/benchmark.png" alt="Bar chart comparing the two benchmark results." />

<!--
-- Invoking fields
-->
### 调用字段

<!--
The fundamental creed of optimization is: "Thou shalt not break correctness."
<span name="monte">Users</span> like it when a language implementation gives
them an answer faster, but only if it's the *right* answer. Alas, our
implementation of faster method invocations fails to uphold that principle:
-->
优化的根本信条是：“汝不可破坏正确性。”<span name="monte">用户</span>喜欢语言实现更快给出答案，但前提是答案是*对的*。唉，我们更快的方法调用实现未能守住这条原则：

```lox
class Oops {
  init() {
    fun f() {
      print "not a method";
    }

    this.field = f;
  }
}

var oops = Oops();
oops.field();
```

<!--
The last line looks like a method call. The compiler thinks that it is and
dutifully emits an `OP_INVOKE` instruction for it. However, it's not. What is
actually happening is a *field* access that returns a function which then gets
called. Right now, instead of executing that correctly, our VM reports a runtime
error when it can't find a method named "field".
-->
最后一行看起来像方法调用。编译器也这么想，乖乖为它发出 `OP_INVOKE`。可它不是。实际发生的是*字段*访问：返回一个函数，再被调用。眼下虚拟机非但不能正确执行，还在找不到名为 `"field"` 的方法时报告运行时错误。

<aside name="monte">

<!--
There are cases where users may be satisfied when a program sometimes returns
the wrong answer in return for running significantly faster or with a better
bound on the performance. These are the field of [**Monte Carlo
algorithms**][monte]. For some use cases, this is a good trade-off.

[monte]: https://en.wikipedia.org/wiki/Monte_Carlo_algorithm

The important part, though, is that the user is *choosing* to apply one of these
algorithms. We language implementers can't unilaterally decide to sacrifice
their program's correctness.
-->
有些情况下，用户可能接受程序偶尔给出错误答案，以换取显著更快或更好的性能上界。那是[**蒙特卡洛算法**][monte]的领域。对某些用例，这是好的权衡。

[monte]: https://en.wikipedia.org/wiki/Monte_Carlo_algorithm

但重要的是：是用户*选择*应用这类算法。我们这些语言实现者不能单方面决定牺牲他们程序的正确性。

</aside>

<!--
Earlier, when we implemented `OP_GET_PROPERTY`, we handled both field and method
accesses. To squash this new bug, we need to do the same thing for `OP_INVOKE`.
-->
先前实现 `OP_GET_PROPERTY` 时，我们同时处理了字段与方法访问。要压掉这个新缺陷，`OP_INVOKE` 也得做同样的事。

^code invoke-field (1 before, 1 after)

<!--
Pretty simple fix. Before looking up a method on the instance's class, we look
for a field with the same name. If we find a field, then we store it on the
stack in place of the receiver, *under* the argument list. This is how
`OP_GET_PROPERTY` behaves since the latter instruction executes before a
subsequent parenthesized list of arguments has been evaluated.
-->
修补相当简单。在实例的类上查找方法之前，先找同名字段。若找到字段，就把它存到栈上取代接收者，位置在参数列表*下面*。这正是 `OP_GET_PROPERTY` 的行为——因为那条指令执行时，后面括号里的参数列表尚未求值。

<!--
Then we try to call that field's value like the callable that it hopefully is.
The `callValue()` helper will check the value's type and call it as appropriate
or report a runtime error if the field's value isn't a callable type like a
closure.
-->
然后我们尝试把该字段的值当作可调用对象来调用。`callValue()` 辅助函数会检查值的类型并酌情调用；若字段值不是闭包之类的可调用类型，就报告运行时错误。

<!--
That's all it takes to make our optimization fully safe. We do sacrifice a
little performance, unfortunately. But that's the price you have to pay
sometimes. You occasionally get frustrated by optimizations you *could* do if
only the language wouldn't allow some annoying corner case. But, as language
<span name="designer">implementers</span>, we have to play the game we're given.
-->
这就足以让优化完全安全。不幸的是，我们确实牺牲了一点性能。但有时这就是必须付的价。你偶尔会懊恼：若语言不许某个烦人的边角情况，本*可以*做的优化。但作为语言<span name="designer">实现者</span>，我们得玩既定的牌。

<aside name="designer">

<!--
As language *designers*, our role is very different. If we do control the
language itself, we may sometimes choose to restrict or change the language in
ways that enable optimizations. Users want expressive languages, but they also
want fast implementations. Sometimes it is good language design to sacrifice a
little power if you can give them perf in return.
-->
作为语言*设计者*，我们的角色很不一样。若我们掌控语言本身，有时可以选择限制或改动语言，好让优化成为可能。用户想要有表达力的语言，也想要快的实现。有时，牺牲一点能力换来性能，正是好的语言设计。

</aside>

<!--
The code we wrote here follows a typical pattern in optimization:

1.  Recognize a common operation or sequence of operations that is performance
    critical. In this case, it is a method access followed by a call.

2.  Add an optimized implementation of that pattern. That's our `OP_INVOKE`
    instruction.

3.  Guard the optimized code with some conditional logic that validates that the
    pattern actually applies. If it does, stay on the fast path. Otherwise, fall
    back to a slower but more robust unoptimized behavior. Here, that means
    checking that we are actually calling a method and not accessing a field.
-->
我们这里写的代码遵循优化里的典型模式：

1.  认出常见且对性能关键的操作或操作序列。这里是方法访问后紧跟调用。

2.  为该模式加上优化实现。那就是我们的 `OP_INVOKE` 指令。

3.  用条件逻辑守护优化代码，验证模式确实适用。适用则留在快路径；否则回退到更慢但更稳健的未优化行为。这里意味着检查我们确实在调用方法，而不是访问字段。

<!--
As your language work moves from getting the implementation working *at all* to
getting it to work *faster*, you will find yourself spending more and more
time looking for patterns like this and adding guarded optimizations for them.
Full-time VM engineers spend much of their careers in this loop.
-->
当你的语言工作从让实现*能跑*转向让它跑*更快*，你会发现自己越来越多时间在寻找这类模式，并为它们加上带守护的优化。全职虚拟机工程师职业生涯的很大一部分，就耗在这个循环里。

<!--
But we can stop here for now. With this, clox now supports most of the features
of an object-oriented programming language, and with respectable performance.
-->
不过眼下可以停在这里。至此，clox 已支持面向对象编程语言的大部分特性，而且性能像样。

<div class="challenges">

<!--
-- Challenges
-->
## 挑战

<!--
1.  The hash table lookup to find a class's `init()` method is constant time,
    but still fairly slow. Implement something faster. Write a benchmark and
    measure the performance difference.

1.  In a dynamically typed language like Lox, a single callsite may invoke a
    variety of methods on a number of classes throughout a program's execution.
    Even so, in practice, most of the time a callsite ends up calling the exact
    same method on the exact same class for the duration of the run. Most calls
    are actually not polymorphic even if the language says they can be.

    How do advanced language implementations optimize based on that observation?

1.  When interpreting an `OP_INVOKE` instruction, the VM has to do two hash
    table lookups. First, it looks for a field that could shadow a method, and
    only if that fails does it look for a method. The former check is rarely
    useful -- most fields do not contain functions. But it is *necessary*
    because the language says fields and methods are accessed using the same
    syntax, and fields shadow methods.

    That is a language *choice* that affects the performance of our
    implementation. Was it the right choice? If Lox were your language, what
    would you do?
-->
1.  查找类的 `init()` 方法的哈希表查找是常量时间，但仍然相当慢。实现更快的做法。写基准并测量性能差异。

1.  在像 Lox 这样的动态类型语言里，单个调用点在程序执行过程中可能调用多个类上的多种方法。即便如此，实践中多数时候，一个调用点在整个运行期间最终调用的仍是同一类上的同一方法。多数调用其实并非多态，即使语言说它们可以是。

    高级语言实现如何基于这一观察做优化？

1.  解释 `OP_INVOKE` 时，虚拟机必须做两次哈希表查找。先找可能遮蔽方法的字段，失败后才找方法。前一次检查很少有用——多数字段并不含函数。但它是*必要的*，因为语言规定字段与方法用同一语法访问，且字段遮蔽方法。

    那是影响实现性能的语言*选择*。那是对的选择吗？若 Lox 是你的语言，你会怎么做？

</div>

<div class="design-note">

<!--
-- Design Note: Novelty Budget
-->
## 设计笔记：新鲜感预算

<!--
I still remember the first time I wrote a tiny BASIC program on a TRS-80 and
made a computer do something it hadn't done before. It felt like a superpower.
The first time I cobbled together just enough of a parser and interpreter to let
me write a tiny program in *my own language* that made a computer do a thing was
like some sort of higher-order meta-superpower. It was and remains a wonderful
feeling.
-->
我仍记得第一次在 TRS-80 上写了一小段 BASIC，让计算机做了它从未做过的事。感觉像超能力。第一次东拼西凑出够用的解析器与解释器，让我能用*自己的语言*写一小段程序、让计算机做点什么——那像某种更高阶的元超能力。那感觉当时美妙，现在依然。

<!--
I realized I could design a language that looked and behaved however I chose. It
was like I'd been going to a private school that required uniforms my whole life
and then one day transferred to a public school where I could wear whatever I
wanted. I don't need to use curly braces for blocks? I can use something other
than an equals sign for assignment? I can do objects without classes? Multiple
inheritance *and* multimethods? A dynamic language that overloads statically, by
arity?
-->
我意识到：我可以设计一门长相与行为都随我心意的语言。像一辈子上要求穿校服的私立学校，有一天转到公立学校，想穿什么穿什么。块不必用花括号？赋值可以用等号以外的东西？可以没有类的对象？多重继承*再加*多方法？一门按元数做静态重载的动态语言？

<!--
Naturally, I took that freedom and ran with it. I made the weirdest, most
arbitrary language design decisions. Apostrophes for generics. No commas between
arguments. Overload resolution that can fail at runtime. I did things
differently just for difference's sake.
-->
自然，我抓着那份自由狂奔。我做了最古怪、最任意的语言设计决定。用撇号表示泛型。参数之间不要逗号。重载决议可以在运行时失败。我为了不同而不同。

<!--
This is a very fun experience that I highly recommend. We need more weird,
avant-garde programming languages. I want to see more art languages. I still
make oddball toy languages for fun sometimes.
-->
这是非常有趣的体验，我强烈推荐。我们需要更多古怪、先锋的编程语言。我想看到更多艺术语言。我偶尔仍会为好玩做些古怪的玩具语言。

<!--
*However*, if your goal is success where "success" is defined as a large number
of users, then your priorities must be different. In that case, your primary
goal is to have your language loaded into the brains of as many people as
possible. That's *really hard*. It takes a lot of human effort to move a
language's syntax and semantics from a computer into trillions of neurons.
-->
*然而*，若你的目标是成功——而“成功”定义为大量用户——那优先级就必须不同。那时你的首要目标是：让尽可能多人的脑子装进你的语言。那*真的很难*。要把一门语言的语法与语义从计算机搬进数万亿神经元，需要大量人力。

<!--
Programmers are naturally conservative with their time and cautious about what
languages are worth uploading into their wetware. They don't want to waste their
time on a language that ends up not being useful to them. As a language
designer, your goal is thus to give them as much language power as you can with
as little required learning as possible.
-->
程序员对自己的时间天生保守，对哪些语言值得上传进湿件也很谨慎。他们不想把时间浪费在最终对自己没用的语言上。于是作为语言设计者，你的目标是：用尽可能少的必学成本，给他们尽可能多的语言能力。

<!--
One natural approach is *simplicity*. The fewer concepts and features your
language has, the less total volume of stuff there is to learn. This is one of
the reasons minimal <span name="dynamic">scripting</span> languages often find
success even though they aren't as powerful as the big industrial languages --
they are easier to get started with, and once they are in someone's brain, the
user wants to keep using them.
-->
一条自然路径是*简洁*。语言的概念与特性越少，要学的总量就越少。这是极简<span name="dynamic">脚本</span>语言即便不如大型工业语言强大却常获成功的原因之一——它们更容易上手；一旦进了某人的脑子，用户就想继续用。

<aside name="dynamic">

<!--
In particular, this is a big advantage of dynamically typed languages. A static
language requires you to learn *two* languages -- the runtime semantics and the
static type system -- before you can get to the point where you are making the
computer do stuff. Dynamic languages require you to learn only the former.

Eventually, programs get big enough that the value of static analysis pays for
the effort to learn that second static language, but the value proposition isn't
as obvious at the outset.
-->
尤其是，这是动态类型语言的一大优势。静态语言要求你学*两门*语言——运行时语义与静态类型系统——才能到让计算机干活的地步。动态语言只需学前者。

最终，程序大到静态分析的价值足以偿还学习那第二门静态语言的成本，但起初价值主张并不那么显而易见。

</aside>

<!--
The problem with simplicity is that simply cutting features often sacrifices
power and expressiveness. There is an art to finding features that punch above
their weight, but often minimal languages simply do less.
-->
简洁的问题在于：单纯砍特性常常牺牲能力与表达力。找出以小搏大的特性是一门艺术，但极简语言往往就是能做的更少。

<!--
There is another path that avoids much of that problem. The trick is to realize
that a user doesn't have to load your entire language into their head, *just the
part they don't already have in there*. As I mentioned in an [earlier design
note][note], learning is about transferring the *delta* between what they
already know and what they need to know.
-->
另有一条路能避开许多这类问题。诀窍是意识到：用户不必把你的整门语言装进脑子，*只需装他们脑子里还没有的那部分*。正如我在[先前的设计笔记][note]里说过：学习是在转移他们已有知识与需要知道的知识之间的*差量*。

[note]: parsing-expressions.html#design-note

<!--
Many potential users of your language already know some other programming
language. Any features your language shares with that language are essentially
"free" when it comes to learning. It's already in their head, they just have to
recognize that your language does the same thing.
-->
你语言的许多潜在用户已经会别的编程语言。你的语言与那门语言共享的任何特性，在学习成本上基本是“免费”的。它已在他们脑子里，只需认出你的语言做同样的事。

<!--
In other words, *familiarity* is another key tool to lower the adoption cost of
your language. Of course, if you fully maximize that attribute, the end result
is a language that is completely identical to some existing one. That's not a
recipe for success, because at that point there's no incentive for users to
switch to your language at all.
-->
换言之，*熟悉感*是降低语言采纳成本的另一关键工具。当然，若把这属性推到极致，最终产物会与某门已有语言完全相同。那不是成功秘方——到那时用户完全没有切换到你语言的动机。

<!--
So you do need to provide some compelling differences. Some things your language
can do that other languages can't, or at least can't do as well. I believe this
is one of the fundamental balancing acts of language design: similarity to other
languages lowers learning cost, while divergence raises the compelling
advantages.
-->
所以你确实需要提供一些有说服力的差异：你的语言能做而其他语言不能、或至少不能做得一样好的事。我认为这是语言设计根本的平衡之一：与其他语言相似降低学习成本，分歧则抬高有说服力的优势。

<!--
I think of this balancing act in terms of a <span name="idiosyncracy">**novelty
budget**</span>, or as Steve Klabnik calls it, a "[strangeness budget][]". Users
have a low threshold for the total amount of new stuff they are willing to
accept to learn a new language. Exceed that, and they won't show up.
-->
我把这种平衡想成<span name="idiosyncracy">**新鲜感预算**</span>，或如 Steve Klabnik 所称的“[怪异预算][strangeness budget]”。用户为学一门新语言愿意接受的新东西总量，阈值很低。超过那个阈值，他们就不会现身。

[strangeness budget]: https://words.steveklabnik.com/the-language-strangeness-budget

<aside name="idiosyncracy">

<!--
A related concept in psychology is [**idiosyncrasy credit**][idiosyncracy], the
idea that other people in society grant you a finite amount of deviations from
social norms. You earn credit by fitting in and doing in-group things, which you
can then spend on oddball activities that might otherwise raise eyebrows. In
other words, demonstrating that you are "one of the good ones" gives you license
to raise your freak flag, but only so far.

[idiosyncracy]: https://en.wikipedia.org/wiki/Idiosyncrasy_credit
-->
心理学里一个相关概念是[**特异信用**][idiosyncracy]：社会中的他人允许你偏离社会规范的额度有限。你通过合群、做圈内事赚取信用，再花在本可能惹人侧目的古怪活动上。换言之，证明你是“自己人”给了你升起怪旗的许可，但也只能到那一步。

[idiosyncracy]: https://en.wikipedia.org/wiki/Idiosyncrasy_credit

</aside>

<!--
Anytime you add something new to your language that other languages don't have,
or anytime your language does something other languages do in a different way,
you spend some of that budget. That's OK -- you *need* to spend it to make your
language compelling. But your goal is to spend it *wisely*. For each feature or
difference, ask yourself how much compelling power it adds to your language and
then evaluate critically whether it pays its way. Is the change so valuable that
it is worth blowing some of your novelty budget?
-->
每当你往语言里加其他语言没有的新东西，或每当你的语言用不同于其他语言的方式做事，你就花掉一些预算。没关系——你*需要*花它，才能让语言有说服力。但目标是*明智地*花。对每个特性或差异，问问自己它为语言增添了多少说服力，再批判地评估它是否划得来。这项改动是否值钱到值得烧掉一部分新鲜感预算？

<!--
In practice, I find this means that you end up being pretty conservative with
syntax and more adventurous with semantics. As fun as it is to put on a new
change of clothes, swapping out curly braces with some other block delimiter is
very unlikely to add much real power to the language, but it does spend some
novelty. It's hard for syntax differences to carry their weight.
-->
实践中，我发现这意味着：你最终会对语法相当保守，对语义更敢冒险。换一身新衣服固然好玩，用别的块定界符替换花括号几乎不太可能给语言增加多少真正能力，却会花掉一些新鲜感。语法差异很难撑起自己的分量。

<!--
On the other hand, new semantics can significantly increase the power of the
language. Multimethods, mixins, traits, reflection, dependent types, runtime
metaprogramming, etc. can radically level up what a user can do with the
language.
-->
另一方面，新语义可以显著提升语言的能力。多方法、mixin、trait、反射、依赖类型、运行时元编程等等，能大幅抬高用户用这门语言能做的事。

<!--
Alas, being conservative like this is not as fun as just changing everything.
But it's up to you to decide whether you want to chase mainstream success or not
in the first place. We don't all need to be radio-friendly pop bands. If you
want your language to be like free jazz or drone metal and are happy with the
proportionally smaller (but likely more devoted) audience size, go for it.
-->
唉，这样保守不如把一切都改掉好玩。但首先要不要追逐主流成功，取决于你。我们不必人人都做电台友好的流行乐队。若你想让语言像自由爵士或 drone metal，并满足于相对更小（但多半更铁杆）的受众规模——尽管去做。

</div>
