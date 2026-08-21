# 调用与函数

<!--
> Any problem in computer science can be solved with another level of
> indirection. Except for the problem of too many layers of indirection.
>
> <cite>David Wheeler</cite>
-->
> 计算机科学里的任何问题，都可以再加一层间接来解决。除了“间接层数太多”这个问题本身。
>
> <cite>大卫·惠勒</cite>

<!--
This chapter is a beast. I try to break features into bite-sized pieces, but
sometimes you gotta swallow the whole <span name="eat">meal</span>. Our next
task is functions. We could start with only function declarations, but that's
not very useful when you can't call them. We could do calls, but there's nothing
to call. And all of the runtime support needed in the VM to support both of
those isn't very rewarding if it isn't hooked up to anything you can see. So
we're going to do it all. It's a lot, but we'll feel good when we're done.
-->
本章是一头猛兽。我尽量把特性拆成一口一口的小块，但有时你得把整<span name="eat">顿饭</span>吞下去。下一桩任务是函数。我们可以只从函数声明下手，可若不能调用，那也没多大用；也可以先做调用，可那时又没有东西可调。而虚拟机里支撑这两头所需的全部运行时设施，若接不上任何看得见的东西，也不会让人觉得划算。所以我们打算一口气全做完。活儿不少，但做完会很畅快。

<aside name="eat">

<!--
Eating -- consumption -- is a weird metaphor for a creative act. But most of the
biological processes that produce "output" are a little less, ahem, decorous.
-->
用“吃”——消费——来比喻创造行为，确实有点怪。不过大多数产生“输出”的生物过程，咳，都没那么体面。

</aside>

<!--
-- Function Objects
-->
## 函数对象

<!--
The most interesting structural change in the VM is around the stack. We already
*have* a stack for local variables and temporaries, so we're partway there. But
we have no notion of a *call* stack. Before we can make much progress, we'll
have to fix that. But first, let's write some code. I always feel better once I
start moving. We can't do much without having some kind of representation for
functions, so we'll start there. From the VM's perspective, what is a function?
-->
虚拟机里最有意思的结构变化，围绕着栈展开。我们*已经*有一个存放局部变量和临时值的栈，所以路已经走了一半。但我们还没有*调用*栈这个概念。要取得实质进展，就得先补上这一点。不过先写点代码吧——一动手，我就觉得踏实。没有某种函数的表示，我们做不了多少事，所以从这儿起步。从虚拟机的角度看，函数究竟是什么？

<!--
A function has a body that can be executed, so that means some bytecode. We
could compile the entire program and all of its function declarations into one
big monolithic Chunk. Each function would have a pointer to the first
instruction of its code inside the Chunk.
-->
函数有一段可执行的函数体，这意味着要有一些字节码。我们可以把整个程序及其全部函数声明，编译进一个硕大的、整块的 Chunk。每个函数各自持有一个指针，指向它在 Chunk 里第一段代码的起始指令。

<!--
This is roughly how compilation to native code works where you end up with one
solid blob of machine code. But for our bytecode VM, we can do something a
little higher level. I think a cleaner model is to give each function its own
Chunk. We'll want some other metadata too, so let's go ahead and stuff it all in
a struct now.
-->
这大致就是编译到原生代码时的做法——最终得到一整坨紧实的机器码。但对我们的字节码虚拟机，可以做得稍稍高阶一点。我认为更干净的模型，是给每个函数各自一块 Chunk。我们还会想要一些别的元数据，所以现在就把它们一股脑塞进一个结构体吧。

^code obj-function (2 before, 2 after)

<!--
Functions are first class in Lox, so they need to be actual Lox objects. Thus
ObjFunction has the same Obj header that all object types share. The `arity`
field stores the number of parameters the function expects. Then, in addition to
the chunk, we store the function's <span name="name">name</span>. That will be
handy for reporting readable runtime errors.
-->
在 Lox 里函数是一等公民，因此它们必须是真正的 Lox 对象。于是 ObjFunction 带着所有对象类型共用的那个 Obj 头。`arity` 字段存放函数期望的参数个数。除了 chunk，我们还保存函数的<span name="name">名字</span>——报告可读的运行时错误时，这会很方便。

<aside name="name">

<!--
Humans don't seem to find numeric bytecode offsets particularly illuminating in
crash dumps.
-->
在崩溃转储里，人类似乎并不觉得那些数字字节码偏移量特别有启发性。

</aside>

<!--
This is the first time the "object" module has needed to reference Chunk, so we
get an include.
-->
这是 “object” 模块第一次需要引用 Chunk，于是我们加一条 include。

^code object-include-chunk (1 before, 1 after)

<!--
Like we did with strings, we define some accessories to make Lox functions
easier to work with in C. Sort of a poor man's object orientation. First, we'll
declare a C function to create a new Lox function.
-->
和字符串时一样，我们定义一些配件，好让 Lox 函数在 C 里更好用——有点穷人版面向对象的意思。首先，声明一个用来创建新 Lox 函数的 C 函数。

^code new-function-h (3 before, 1 after)

<!--
The implementation is over here:
-->
实现在这边：

^code new-function

<!--
We use our friend `ALLOCATE_OBJ()` to allocate memory and initialize the
object's header so that the VM knows what type of object it is. Instead of
passing in arguments to initialize the function like we did with ObjString, we
set the function up in a sort of blank state -- zero arity, no name, and no
code. That will get filled in later after the function is created.
-->
我们用老朋友 `ALLOCATE_OBJ()` 分配内存并初始化对象头，好让虚拟机知道这是什么类型的对象。不像 ObjString 那样传入参数来初始化，我们把函数摆成一种空白状态——零 arity、没有名字、没有代码。这些会在函数创建之后再填上。

<!--
Since we have a new kind of object, we need a new object type in the enum.
-->
既然有了一种新对象，枚举里就需要一个新的对象类型。

^code obj-type-function (1 before, 2 after)

<!--
When we're done with a function object, we must return the bits it borrowed back
to the operating system.
-->
用完一个函数对象后，必须把它借来的那些比特还给操作系统。

^code free-function (1 before, 1 after)

<!--
This switch case is <span name="free-name">responsible</span> for freeing the
ObjFunction itself as well as any other memory it owns. Functions own their
chunk, so we call Chunk's destructor-like function.
-->
这个 switch 分支<span name="free-name">负责</span>释放 ObjFunction 本身，以及它拥有的其他内存。函数拥有自己的 chunk，所以我们调用 Chunk 那类似析构的函数。

<aside name="free-name">

<!--
We don't need to explicitly free the function's name because it's an ObjString.
That means we can let the garbage collector manage its lifetime for us. Or, at
least, we'll be able to once we [implement a garbage collector][gc].

[gc]: garbage-collection.html
-->
我们不必显式释放函数的名字，因为它是 ObjString。这意味着可以把寿命交给垃圾收集器管理——或者说，等我们[实现了垃圾收集器][gc]之后就能这么做。

[gc]: garbage-collection.html

</aside>

<!--
Lox lets you print any object, and functions are first-class objects, so we
need to handle them too.
-->
Lox 允许你打印任何对象，而函数是一等对象，所以我们也得处理它们。

^code print-function (1 before, 1 after)

<!--
This calls out to:
-->
它转去调用：

^code print-function-helper

<!--
Since a function knows its name, it may as well say it.
-->
既然函数知道自己的名字，不妨就报上名来。

<!--
Finally, we have a couple of macros for converting values to functions. First,
make sure your value actually *is* a function.
-->
最后，还有几条宏用来把值转换成函数。首先，确认你的值*确实*是一个函数。

^code is-function (2 before, 1 after)

<!--
Assuming that evaluates to true, you can then safely cast the Value to an
ObjFunction pointer using this:
-->
若求值结果为真，就可以用这条宏安全地把 Value 转成 ObjFunction 指针：

^code as-function (2 before, 1 after)

<!--
With that, our object model knows how to represent functions. I'm feeling warmed
up now. You ready for something a little harder?
-->
至此，我们的对象模型知道如何表示函数了。我觉得热身得差不多了。准备好来点更难的了吗？

<!--
-- Compiling to Function Objects
-->
## 编译为函数对象

<!--
Right now, our compiler assumes it is always compiling to one single chunk. With
each function's code living in separate chunks, that gets more complex. When the
compiler reaches a function declaration, it needs to emit code into the
function's chunk when compiling its body. At the end of the function body, the
compiler needs to return to the previous chunk it was working with.
-->
眼下，编译器假定自己始终在往单独一块 chunk 里编译。一旦每个函数的代码各自住在独立的 chunk 里，事情就复杂起来了。编译器碰到函数声明时，编译函数体要往该函数的 chunk 里发射代码；函数体结束时，又得回到先前正在处理的那块 chunk。

<!--
That's fine for code inside function bodies, but what about code that isn't? The
"top level" of a Lox program is also imperative code and we need a chunk to
compile that into. We can simplify the compiler and VM by placing that top-level
code inside an automatically defined function too. That way, the compiler is
always within some kind of function body, and the VM always runs code by
invoking a function. It's as if the entire program is <span
name="wrap">wrapped</span> inside an implicit `main()` function.
-->
对函数体里的代码这没问题，但那些不在函数体里的呢？Lox 程序的“顶层”同样是命令式代码，我们也需要一块 chunk 来编译它。可以把这段顶层代码也塞进一个自动定义的函数里，从而简化编译器和虚拟机。这样一来，编译器始终处在某种函数体中，虚拟机也总是通过调用函数来跑代码——仿佛整个程序都被<span name="wrap">包</span>在一个隐式的 `main()` 里。

<aside name="wrap">

<!--
One semantic corner where that analogy breaks down is global variables. They
have special scoping rules different from local variables, so in that way, the
top level of a script isn't like a function body.
-->
这个类比在语义上有一处说不通：全局变量。它们有不同于局部变量的特殊作用域规则，因此脚本顶层并不完全像函数体。

</aside>

<!--
Before we get to user-defined functions, then, let's do the reorganization to
support that implicit top-level function. It starts with the Compiler struct.
Instead of pointing directly to a Chunk that the compiler writes to, it instead
has a reference to the function object being built.
-->
那么，在动手用户自定义函数之前，先做这番重组，以支撑那个隐式的顶层函数。从 Compiler 结构体开始：它不再直接指向编译器要写入的 Chunk，而是持有一份对正在构建的函数对象的引用。

^code function-fields (1 before, 1 after)

<!--
We also have a little FunctionType enum. This lets the compiler tell when it's
compiling top-level code versus the body of a function. Most of the compiler
doesn't care about this -- that's why it's a useful abstraction -- but in one or
two places the distinction is meaningful. We'll get to one later.
-->
我们还有一个小小的 FunctionType 枚举。它让编译器能分辨自己是在编译顶层代码，还是某个函数的函数体。编译器的大部分地方并不在意这一点——正因为如此，它才是个有用的抽象——但在一两处地方，这个区分意义重大。稍后我们会碰到其中一处。

^code function-type-enum

<!--
Every place in the compiler that was writing to the Chunk now needs to go
through that `function` pointer. Fortunately, many <span
name="current">chapters</span> ago, we encapsulated access to the chunk in the
`currentChunk()` function. We only need to fix that and the rest of the compiler
is happy.
-->
编译器里凡是往 Chunk 写东西的地方，如今都要经由那个 `function` 指针。所幸，许多<span name="current">章</span>以前，我们就把对 chunk 的访问封装进了 `currentChunk()`。只需修好这一处，编译器其余部分就会高高兴兴。

<aside name="current">

<!--
It's almost like I had a crystal ball that could see into the future and knew
we'd need to change the code later. But, really, it's because I wrote all the
code for the book before any of the text.
-->
简直像我有一颗水晶球，能窥见未来，知道我们以后要改这段代码。其实呢，是因为我先写完了全书所有代码，才动手写正文。

</aside>

^code current-chunk (1 before, 2 after)

<!--
The current chunk is always the chunk owned by the function we're in the middle
of compiling. Next, we need to actually create that function. Previously, the VM
passed a Chunk to the compiler which filled it with code. Instead, the compiler
will create and return a function that contains the compiled top-level code --
which is all we support right now -- of the user's program.
-->
当前 chunk 始终是我们正在编译的那个函数所拥有的 chunk。接下来，得真正创建那个函数。从前，虚拟机传给编译器一块 Chunk，由编译器往里填代码；如今改为由编译器创建并返回一个函数，里面装着用户程序已编译好的顶层代码——眼下我们也就支持这一种。

<!--
-- Creating functions at compile time
-->
### 在编译期创建函数

<!--
We start threading this through in `compile()`, which is the main entry point
into the compiler.
-->
我们从 `compile()` 开始把这套改动穿起来——它是进入编译器的主入口。

^code call-init-compiler (1 before, 2 after)

<!--
There are a bunch of changes in how the compiler is initialized. First, we
initialize the new Compiler fields.
-->
编译器的初始化方式有一堆改动。首先，初始化那些新的 Compiler 字段。

^code init-compiler (1 after)

<!--
Then we allocate a new function object to compile into.
-->
然后分配一个新的函数对象，作为编译的目标。

^code init-function (1 before, 1 after)

<span name="null"></span>

<aside name="null">

<!--
I know, it looks dumb to null the `function` field only to immediately assign it
a value a few lines later. More garbage collection-related paranoia.
-->
我知道，把 `function` 字段先置空，几行后又立刻赋值，看起来挺傻。这更多是与垃圾收集相关的 paranoia。

</aside>

<!--
Creating an ObjFunction in the compiler might seem a little strange. A function
object is the *runtime* representation of a function, but here we are creating
it at compile time. The way to think of it is that a function is similar to a
string or number literal. It forms a bridge between the compile time and runtime
worlds. When we get to function *declarations*, those really *are* literals
-- they are a notation that produces values of a built-in type. So the <span
name="closure">compiler</span> creates function objects during compilation.
Then, at runtime, they are simply invoked.
-->
在编译器里创建 ObjFunction，乍看有点怪。函数对象是函数的*运行时*表示，可我们却在编译期创建它。不妨这样想：函数类似于字符串或数字字面量，它在编译期世界与运行时世界之间架起一座桥。等我们做到函数*声明*时，那些声明其实*就是*字面量——一种产生内置类型值的记法。因此<span name="closure">编译器</span>在编译期间创建函数对象；到了运行时，只需调用它们即可。

<aside name="closure">

<!--
We can create functions at compile time because they contain only data available
at compile time. The function's code, name, and arity are all fixed. When we add
closures in the [next chapter][closures], which capture variables at runtime,
the story gets more complex.

[closures]: closures.html
-->
我们能在编译期创建函数，是因为它们只包含编译期可得的数据。函数的代码、名字和 arity 都是固定的。等[下一章][closures]加入在运行时捕获变量的闭包时，故事就会更复杂。

[closures]: closures.html

</aside>

<!--
Here is another strange piece of code:
-->
这里还有一段古怪的代码：

^code init-function-slot (1 before, 1 after)

<!--
Remember that the compiler's `locals` array keeps track of which stack slots are
associated with which local variables or temporaries. From now on, the compiler
implicitly claims stack slot zero for the VM's own internal use. We give it an
empty name so that the user can't write an identifier that refers to it. I'll
explain what this is about when it becomes useful.
-->
别忘了，编译器的 `locals` 数组跟踪着哪些栈槽对应哪些局部变量或临时值。从现在起，编译器隐式占下栈槽零，供虚拟机自己内部使用。我们给它一个空名字，好让用户写不出能引用它的标识符。等它派上用场时，我再解释这是怎么回事。

<!--
That's the initialization side. We also need a couple of changes on the other
end when we finish compiling some code.
-->
这是初始化那一头。编译完某段代码时，另一头也需要几处改动。

^code end-compiler (1 after)

<!--
Previously, when `interpret()` called into the compiler, it passed in a Chunk to
be written to. Now that the compiler creates the function object itself, we
return that function. We grab it from the current compiler here:
-->
从前，`interpret()` 调用编译器时，会传入一块要写入的 Chunk。如今编译器自己创建函数对象，我们就返回那个函数。从当前编译器里把它取出来：

^code end-function (1 before, 1 after)

<!--
And then return it to `compile()` like so:
-->
然后像这样返回给 `compile()`：

^code return-function (1 before, 1 after)

<!--
Now is a good time to make another tweak in this function. Earlier, we added
some diagnostic code to have the VM dump the disassembled bytecode so we could
debug the compiler. We should fix that to keep working now that the generated
chunk is wrapped in a function.
-->
现在是个好时机，给这个函数再做一处微调。早些时候，我们加过一些诊断代码，让虚拟机转储反汇编后的字节码，以便调试编译器。既然生成的 chunk 已被包进函数里，这块也得修好，让它继续工作。

^code disassemble-end (2 before, 2 after)

<!--
Notice the check in here to see if the function's name is `NULL`? User-defined
functions have names, but the implicit function we create for the top-level code
does not, and we need to handle that gracefully even in our own diagnostic code.
Speaking of which:
-->
注意到这里检查函数名是否为 `NULL` 了吗？用户定义的函数有名字，但我们为顶层代码创建的那个隐式函数没有；即便在我们自己的诊断代码里，也得优雅地处理这一点。说到这个：

^code print-script (1 before, 1 after)

<!--
There's no way for a *user* to get a reference to the top-level function and try
to print it, but our `DEBUG_TRACE_EXECUTION` <span
name="debug">diagnostic</span> code that prints the entire stack can and does.
-->
*用户*没法拿到顶层函数的引用再去打印它，但我们那打印整个栈的 `DEBUG_TRACE_EXECUTION` <span name="debug">诊断</span>代码可以，而且确实会这么做。

<aside name="debug">

<!--
It is no fun if the diagnostic code we use to find bugs itself causes the VM to
segfault!
-->
用来找 bug 的诊断代码自己把虚拟机搞成段错误，可就不好玩了！

</aside>

<!--
Bumping up a level to `compile()`, we adjust its signature.
-->
往上提一层到 `compile()`，我们调整它的签名。

^code compile-h (2 before, 2 after)

<!--
Instead of taking a chunk, now it returns a function. Over in the
implementation:
-->
它不再接收一块 chunk，而是返回一个函数。实现这边：

^code compile-signature (1 after)

<!--
Finally we get to some actual code. We change the very end of the function to
this:
-->
终于写到一点实际代码了。把函数的末尾改成这样：

^code call-end-compiler (4 before, 1 after)

<!--
We get the function object from the compiler. If there were no compile errors,
we return it. Otherwise, we signal an error by returning `NULL`. This way, the
VM doesn't try to execute a function that may contain invalid bytecode.
-->
我们从编译器拿到函数对象。若没有编译错误，就返回它；否则返回 `NULL` 表示出错。这样虚拟机就不会去执行可能含有无效字节码的函数。

<!--
Eventually, we will update `interpret()` to handle the new declaration of
`compile()`, but first we have some other changes to make.
-->
最终我们会更新 `interpret()` 以适配 `compile()` 的新声明，但先还有别的改动要做。

<!--
-- Call Frames
-->
## 调用帧

<!--
It's time for a big conceptual leap. Before we can implement function
declarations and calls, we need to get the VM ready to handle them. There are
two main problems we need to worry about:
-->
该迈出一大步概念上的飞跃了。在实现函数声明与调用之前，得先让虚拟机准备好处理它们。我们主要要操心两个问题：

<!--
-- Allocating local variables
-->
### 分配局部变量

<!--
The compiler allocates stack slots for local variables. How should that work
when the set of local variables in a program is distributed across multiple
functions?
-->
编译器为局部变量分配栈槽。当程序里的局部变量分散在多个函数中时，这该怎么运作？

<!--
One option would be to keep them totally separate. Each function would get its
own dedicated set of slots in the VM stack that it would own <span
name="static">forever</span>, even when the function isn't being called. Each
local variable in the entire program would have a bit of memory in the VM that
it keeps to itself.
-->
一种办法是把它们完全分开。每个函数在虚拟机栈上各有一套专属槽位，即便函数没被调用，也<span name="static">永远</span>占着。整个程序里的每个局部变量，在虚拟机里都有一小块只属于自己的内存。

<aside name="static">

<!--
It's basically what you'd get if you declared every local variable in a C
program using `static`.
-->
基本上就等于你在 C 程序里把每个局部变量都用 `static` 声明。

</aside>

<!--
Believe it or not, early programming language implementations worked this way.
The first Fortran compilers statically allocated memory for each variable. The
obvious problem is that it's really inefficient. Most functions are not in the
middle of being called at any point in time, so sitting on unused memory for
them is wasteful.
-->
信不信由你，早期的编程语言实现就是这么干的。最早的 Fortran 编译器为每个变量静态分配内存。显而易见的问题是：这非常低效。在任意时刻，大多数函数并不处在被调用的过程中，白白占着不用的内存，实在浪费。

<!--
The more fundamental problem, though, is recursion. With recursion, you can be
"in" multiple calls to the same function at the same time. Each needs its <span
name="fortran">own</span> memory for its local variables. In jlox, we solved
this by dynamically allocating memory for an environment each time a function
was called or a block entered. In clox, we don't want that kind of performance
cost on every function call.
-->
不过更根本的问题是递归。有了递归，你可以同时“身处”对同一函数的多次调用之中。每一次都需要<span name="fortran">自己的</span>局部变量内存。在 jlox 里，我们每次调用函数或进入块时动态分配环境，以此解决。在 clox 里，我们不想在每次函数调用上都付这种性能代价。

<aside name="fortran">

<!--
Fortran avoided this problem by disallowing recursion entirely. Recursion was
considered an advanced, esoteric feature at the time.
-->
Fortran 干脆禁止递归，从而回避了这个问题。当时递归被视为一种高深、偏门的特性。

</aside>

<!--
Instead, our solution lies somewhere between Fortran's static allocation and
jlox's dynamic approach. The value stack in the VM works on the observation that
local variables and temporaries behave in a last-in first-out fashion.
Fortunately for us, that's still true even when you add function calls into the
mix. Here's an example:
-->
我们的方案介于 Fortran 的静态分配与 jlox 的动态做法之间。虚拟机里的值栈，基于这样一个观察：局部变量和临时值按后进先出的方式行事。对我们来说幸运的是，即便掺进函数调用，这一点依然成立。来看个例子：

```lox
fun first() {
  var a = 1;
  second();
  var b = 2;
}

fun second() {
  var c = 3;
  var d = 4;
}

first();
```

<!--
Step through the program and look at which variables are in memory at each point
in time:
-->
一步步走这个程序，看看每个时刻内存里有哪些变量：

<img src="image/calls-and-functions/calls.png" alt="Tracing through the execution of the previous program, showing the stack of variables at each step." />

<!--
As execution flows through the two calls, every local variable obeys the
principle that any variable declared after it will be discarded before the first
variable needs to be. This is true even across calls. We know we'll be done with
`c` and `d` before we are done with `a`. It seems we should be able to allocate
local variables on the VM's value stack.
-->
随着执行流经这两次调用，每个局部变量都遵守这样一条原则：在它之后声明的任何变量，都会在第一个变量需要被丢弃之前先被丢弃。即便跨越调用，这也成立。我们知道，在用完 `a` 之前，`c` 和 `d` 早已用完。看来，我们应当能在虚拟机的值栈上分配局部变量。

<!--
Ideally, we still determine *where* on the stack each variable will go at
compile time. That keeps the bytecode instructions for working with variables
simple and fast. In the above example, we could <span
name="imagine">imagine</span> doing so in a straightforward way, but that
doesn't always work out. Consider:
-->
理想情况下，我们仍想在编译期就确定每个变量会落在栈的*哪里*。这样，操作变量的字节码指令就能保持简单而快速。在上面的例子里，我们可以<span name="imagine">想象</span>用直截了当的方式做到这一点，但并非总能如愿。请看：

<aside name="imagine">

<!--
I say "imagine" because the compiler can't actually figure this out. Because
functions are first class in Lox, we can't determine which functions call which
others at compile time.
-->
我说“想象”，是因为编译器其实算不出来。Lox 里函数是一等公民，我们无法在编译期确定哪些函数会调用哪些别的函数。

</aside>

```lox
fun first() {
  var a = 1;
  second();
  var b = 2;
  second();
}

fun second() {
  var c = 3;
  var d = 4;
}

first();
```

<!--
In the first call to `second()`, `c` and `d` would go into slots 1 and 2. But in
the second call, we need to have made room for `b`, so `c` and `d` need to be in
slots 2 and 3. Thus the compiler can't pin down an exact slot for each local
variable across function calls. But *within* a given function, the *relative*
locations of each local variable are fixed. Variable `d` is always in the slot
right after `c`. This is the key insight.
-->
第一次调用 `second()` 时，`c` 和 `d` 会进槽 1 和 2。但第二次调用时，我们得先给 `b` 腾地方，于是 `c` 和 `d` 需要落在槽 2 和 3。因此，编译器无法跨函数调用，为每个局部变量钉死一个确切的槽位。但在*同一个*函数*内部*，各局部变量的*相对*位置是固定的。变量 `d` 总是紧挨在 `c` 之后的那个槽。这就是关键洞见。

<!--
When a function is called, we don't know where the top of the stack will be
because it can be called from different contexts. But, wherever that top happens
to be, we do know where all of the function's local variables will be relative
to that starting point. So, like many problems, we solve our allocation problem
with a level of indirection.
-->
函数被调用时，我们不知道栈顶会在哪里，因为它可能从不同上下文被调用。但无论那个顶恰好在哪，我们都知道，相对那个起点，函数的全部局部变量会落在哪里。于是，像许多问题一样，我们用一层间接来解决分配问题。

<!--
At the beginning of each function call, the VM records the location of the first
slot where that function's own locals begin. The instructions for working with
local variables access them by a slot index relative to that, instead of
relative to the bottom of the stack like they do today. At compile time, we
calculate those relative slots. At runtime, we convert that relative slot to an
absolute stack index by adding the function call's starting slot.
-->
每次函数调用开始时，虚拟机记下该函数自己的局部变量起始的第一个槽的位置。操作局部变量的指令，按相对这个位置的槽下标来访问，而不再像今天这样相对栈底。编译期我们算出这些相对槽；运行时，把相对槽加上本次调用的起始槽，就得到绝对栈下标。

<!--
It's as if the function gets a "window" or "frame" within the larger stack where
it can store its locals. The position of the **call frame** is determined at
runtime, but within and relative to that region, we know where to find things.
-->
仿佛函数在更大的栈里得到了一扇“窗口”或一个“帧”，用来存放自己的局部变量。**调用帧**的位置在运行时确定，但在那个区域内、相对那个区域，我们知道东西在哪儿。

<img src="image/calls-and-functions/window.png" alt="The stack at the two points when second() is called, with a window hovering over each one showing the pair of stack slots used by the function." />

<!--
The historical name for this recorded location where the function's locals start
is a **frame pointer** because it points to the beginning of the function's call
frame. Sometimes you hear **base pointer**, because it points to the base stack
slot on top of which all of the function's variables live.
-->
这个记录下来的、函数局部变量起始位置的历史名称，叫做**帧指针**（frame pointer），因为它指向函数调用帧的开头。有时你会听到**基指针**（base pointer），因为它指向基栈槽——函数的全部变量都叠在它之上。

<!--
That's the first piece of data we need to track. Every time we call a function,
the VM determines the first stack slot where that function's variables begin.
-->
这是我们需要跟踪的第一块数据。每次调用函数时，虚拟机确定该函数变量起始的第一个栈槽。

<!--
-- Return addresses
-->
### 返回地址

<!--
Right now, the VM works its way through the instruction stream by incrementing
the `ip` field. The only interesting behavior is around control flow
instructions which offset the `ip` by larger amounts. *Calling* a function is
pretty straightforward -- simply set `ip` to point to the first instruction in
that function's chunk. But what about when the function is done?
-->
眼下，虚拟机靠递增 `ip` 字段在指令流里往前走。唯一有点意思的行为，是那些把 `ip` 偏移较大距离的控制流指令。*调用*一个函数相当直截了当——只需把 `ip` 设成指向该函数 chunk 里的第一条指令。但函数跑完了呢？

<!--
The VM needs to <span name="return">return</span> back to the chunk where the
function was called from and resume execution at the instruction immediately
after the call. Thus, for each function call, we need to track where we jump
back to when the call completes. This is called a **return address** because
it's the address of the instruction that the VM returns to after the call.
-->
虚拟机需要<span name="return">返回</span>到当初调用该函数的那个 chunk，并从紧跟在调用之后的那条指令恢复执行。因此，对每次函数调用，我们都要跟踪调用完成时该跳回哪里。这叫做**返回地址**，因为它是虚拟机在调用结束后返回去执行的那条指令的地址。

<!--
Again, thanks to recursion, there may be multiple return addresses for a single
function, so this is a property of each *invocation* and not the function
itself.
-->
同样，多亏递归，同一个函数可能有多个返回地址，所以这是每次*调用*的属性，而非函数本身的属性。

<aside name="return">

<!--
The authors of early Fortran compilers had a clever trick for implementing
return addresses. Since they *didn't* support recursion, any given function
needed only a single return address at any point in time. So when a function was
called at runtime, the program would *modify its own code* to change a jump
instruction at the end of the function to jump back to its caller. Sometimes the
line between genius and madness is hair thin.
-->
早期 Fortran 编译器的作者们实现返回地址时有个巧妙招数。既然他们*不*支持递归，任一函数在任一时刻只需要一个返回地址。于是函数在运行时被调用时，程序会*修改自己的代码*，把函数末尾的一条跳转指令改成跳回调用者。天才与疯狂之间的界线，有时细如发丝。

</aside>

<!--
-- The call stack
-->
### 调用栈

<!--
So for each live function invocation -- each call that hasn't returned yet -- we
need to track where on the stack that function's locals begin, and where the
caller should resume. We'll put this, along with some other stuff, in a new
struct.
-->
因此，对每一次仍在进行的函数调用——每一次尚未返回的调用——我们都要跟踪该函数的局部变量在栈上从哪里开始，以及调用者应从哪里恢复。我们把这些连同别的一些东西，放进一个新结构体。

^code call-frame (1 before, 2 after)

<!--
A CallFrame represents a single ongoing function call. The `slots` field points
into the VM's value stack at the first slot that this function can use. I gave
it a plural name because -- thanks to C's weird "pointers are sort of arrays"
thing -- we'll treat it like an array.
-->
一个 CallFrame 表示一次正在进行的函数调用。`slots` 字段指向虚拟机值栈上该函数可用的第一个槽。我给它起了个复数名字——多亏 C 那种古怪的“指针有点像数组”的特性——我们会把它当数组来用。

<!--
The implementation of return addresses is a little different from what I
described above. Instead of storing the return address in the callee's frame,
the caller stores its own `ip`. When we return from a function, the VM will jump
to the `ip` of the caller's CallFrame and resume from there.
-->
返回地址的实现，与我上面描述的略有不同。我们并不把返回地址存在被调用者的帧里，而是由调用者保存自己的 `ip`。从函数返回时，虚拟机跳到调用者 CallFrame 的 `ip`，从那里恢复。

<!--
I also stuffed a pointer to the function being called in here. We'll use that to
look up constants and for a few other things.
-->
我还往这里塞了一个指向被调用函数的指针。我们会用它查找常量，以及做几件别的事。

<!--
Each time a function is called, we create one of these structs. We could <span
name="heap">dynamically</span> allocate them on the heap, but that's slow.
Function calls are a core operation, so they need to be as fast as possible.
Fortunately, we can make the same observation we made for variables: function
calls have stack semantics. If `first()` calls `second()`, the call to
`second()` will complete before `first()` does.
-->
每次调用函数，我们就创建一个这样的结构体。可以<span name="heap">动态</span>在堆上分配它们，但那样慢。函数调用是核心操作，必须尽可能快。所幸，我们可以做与变量时相同的观察：函数调用具有栈语义。若 `first()` 调用 `second()`，对 `second()` 的调用会在 `first()` 结束之前完成。

<aside name="heap">

<!--
Many Lisp implementations dynamically allocate stack frames because it
simplifies implementing [continuations][cont]. If your language supports
continuations, then function calls do *not* always have stack semantics.

[cont]: https://en.wikipedia.org/wiki/Continuation
-->
许多 Lisp 实现动态分配栈帧，因为这能简化[续体][cont]的实现。若你的语言支持续体，函数调用就*不*总是具有栈语义。

[cont]: https://en.wikipedia.org/wiki/Continuation

</aside>

<!--
So over in the VM, we create an array of these CallFrame structs up front and
treat it as a stack, like we do with the value array.
-->
于是在虚拟机这边，我们预先创建这些 CallFrame 结构体的数组，并像值数组那样把它当作栈来用。

^code frame-array (1 before, 1 after)

<!--
This array replaces the `chunk` and `ip` fields we used to have directly in the
VM. Now each CallFrame has its own `ip` and its own pointer to the ObjFunction
that it's executing. From there, we can get to the function's chunk.
-->
这个数组取代了我们从前直接放在虚拟机里的 `chunk` 和 `ip` 字段。如今每个 CallFrame 有自己的 `ip`，以及指向正在执行的 ObjFunction 的指针。从那儿就能到达函数的 chunk。

<!--
The new `frameCount` field in the VM stores the current height of the CallFrame
stack -- the number of ongoing function calls. To keep clox simple, the array's
capacity is fixed. This means, as in many language implementations, there is a
maximum call depth we can handle. For clox, it's defined here:
-->
虚拟机里新的 `frameCount` 字段存放 CallFrame 栈当前的高度——即正在进行的函数调用个数。为保持 clox 简单，数组容量是固定的。这意味着，像许多语言实现一样，我们能处理的调用深度有上限。对 clox，它定义在这里：

^code frame-max (2 before, 2 after)

<!--
We also redefine the value stack's <span name="plenty">size</span> in terms of
that to make sure we have plenty of stack slots even in very deep call trees.
When the VM starts up, the CallFrame stack is empty.
-->
我们还据此重新定义值栈的<span name="plenty">大小</span>，确保即便在很深的调用树里，也有充足的栈槽。虚拟机启动时，CallFrame 栈是空的。

<aside name="plenty">

<!--
It is still possible to overflow the stack if enough function calls use enough
temporaries in addition to locals. A robust implementation would guard against
this, but I'm trying to keep things simple.
-->
若足够多的函数调用除了局部变量还用了足够多的临时值，栈仍有可能溢出。稳健的实现会防范这一点，但我尽量保持简单。

</aside>

^code reset-frame-count (1 before, 1 after)

<!--
The "vm.h" header needs access to ObjFunction, so we add an include.
-->
“vm.h” 头文件需要访问 ObjFunction，于是我们加一条 include。

^code vm-include-object (2 before, 1 after)

<!--
Now we're ready to move over to the VM's implementation file. We've got some
grunt work ahead of us. We've moved `ip` out of the VM struct and into
CallFrame. We need to fix every line of code in the VM that touches `ip` to
handle that. Also, the instructions that access local variables by stack slot
need to be updated to do so relative to the current CallFrame's `slots` field.
-->
现在可以转到虚拟机的实现文件了。前面有些苦活。我们已把 `ip` 从 VM 结构体挪进 CallFrame。虚拟机里每一处碰到 `ip` 的代码都得修好以适配这一点。此外，那些按栈槽访问局部变量的指令，也要改成相对当前 CallFrame 的 `slots` 字段来访问。

<!--
We'll start at the top and plow through it.
-->
我们从顶上开始，一路犁过去。

^code run (1 before, 1 after)

<!--
First, we store the current topmost CallFrame in a <span
name="local">local</span> variable inside the main bytecode execution function.
Then we replace the bytecode access macros with versions that access `ip`
through that variable.
-->
首先，在主字节码执行函数里，把当前最顶层的 CallFrame 存进一个<span name="local">局部</span>变量。然后把字节码访问宏换成经由该变量访问 `ip` 的版本。

<aside name="local">

<!--
We could access the current frame by going through the CallFrame array every
time, but that's verbose. More importantly, storing the frame in a local
variable encourages the C compiler to keep that pointer in a register. That
speeds up access to the frame's `ip`. There's no *guarantee* that the compiler
will do this, but there's a good chance it will.
-->
我们本可以每次都经由 CallFrame 数组去访问当前帧，但那样啰嗦。更重要的是，把帧存在局部变量里，会鼓励 C 编译器把那个指针留在寄存器里，从而加速对帧的 `ip` 的访问。编译器*不保证*会这么做，但很有机会。

</aside>

<!--
Now onto each instruction that needs a little tender loving care.
-->
接下来是每条需要一点温柔呵护的指令。

^code push-local (2 before, 1 after)

<!--
Previously, `OP_GET_LOCAL` read the given local slot directly from the VM's
stack array, which meant it indexed the slot starting from the bottom of the
stack. Now, it accesses the current frame's `slots` array, which means it
accesses the given numbered slot relative to the beginning of that frame.
-->
从前，`OP_GET_LOCAL` 直接从虚拟机的栈数组读取给定的局部槽，也就是从栈底起算下标。如今它访问当前帧的 `slots` 数组，也就是相对该帧起点去访问给定编号的槽。

<!--
Setting a local variable works the same way.
-->
设置局部变量也是同一套路。

^code set-local (2 before, 1 after)

<!--
The jump instructions used to modify the VM's `ip` field. Now, they do the same
for the current frame's `ip`.
-->
跳转指令从前修改虚拟机的 `ip` 字段。如今它们对当前帧的 `ip` 做同样的事。

^code jump (2 before, 1 after)

<!--
Same with the conditional jump:
-->
条件跳转也一样：

^code jump-if-false (2 before, 1 after)

<!--
And our backward-jumping loop instruction:
-->
还有我们那条向后跳的循环指令：

^code loop (2 before, 1 after)

<!--
We have some diagnostic code that prints each instruction as it executes to help
us debug our VM. That needs to work with the new structure too.
-->
我们有一些诊断代码，在执行时打印每条指令，好帮我们调试虚拟机。它也得适配新结构。

^code trace-execution (1 before, 1 after)

<!--
Instead of passing in the VM's `chunk` and `ip` fields, now we read from the
current CallFrame.
-->
不再传入虚拟机的 `chunk` 和 `ip` 字段，而是从当前 CallFrame 读取。

<!--
You know, that wasn't too bad, actually. Most instructions just use the macros
so didn't need to be touched. Next, we jump up a level to the code that calls
`run()`.
-->
其实没那么糟。大多数指令只用宏，所以不用动。接下来往上跳一层，到调用 `run()` 的代码。

^code interpret-stub (1 before, 2 after)

<!--
We finally get to wire up our earlier compiler changes to the back-end changes
we just made. First, we pass the source code to the compiler. It returns us a
new ObjFunction containing the compiled top-level code. If we get `NULL` back,
it means there was some compile-time error which the compiler has already
reported. In that case, we bail out since we can't run anything.
-->
终于可以把早先的编译器改动，接到我们刚做的后端改动上了。首先，把源码交给编译器。它返回一个新的 ObjFunction，装着已编译的顶层代码。若得到 `NULL`，说明有编译期错误，编译器已经报告过了。这种情况下我们收工走人，因为什么也跑不了。

<!--
Otherwise, we store the function on the stack and prepare an initial CallFrame
to execute its code. Now you can see why the compiler sets aside stack slot zero
-- that stores the function being called. In the new CallFrame, we point to the
function, initialize its `ip` to point to the beginning of the function's
bytecode, and set up its stack window to start at the very bottom of the VM's
value stack.
-->
否则，我们把函数存到栈上，并准备一个初始 CallFrame 来执行它的代码。现在你能明白编译器为何预留栈槽零了——那里存放正在被调用的函数。在新的 CallFrame 里，我们指向该函数，把它的 `ip` 初始化为指向函数字节码的开头，并把它的栈窗口设成从虚拟机值栈的最底部开始。

<!--
This gets the interpreter ready to start executing code. After finishing, the VM
used to free the hardcoded chunk. Now that the ObjFunction owns that code, we
don't need to do that anymore, so the end of `interpret()` is simply this:
-->
这就让解释器准备好开始执行代码了。从前结束后，虚拟机会释放那块硬编码的 chunk。如今 ObjFunction 拥有那段代码，我们不必再那么做，于是 `interpret()` 的末尾就简单地变成这样：

^code end-interpret (2 before, 1 after)

<!--
The last piece of code referring to the old VM fields is `runtimeError()`. We'll
revisit that later in the chapter, but for now let's change it to this:
-->
最后一处引用旧 VM 字段的代码是 `runtimeError()`。本章稍后还会再访它，眼下先改成这样：

^code runtime-error-temp (2 before, 1 after)

<!--
Instead of reading the chunk and `ip` directly from the VM, it pulls those from
the topmost CallFrame on the stack. That should get the function working again
and behaving as it did before.
-->
它不再直接从虚拟机读 chunk 和 `ip`，而是从栈上最顶层的 CallFrame 取。这应能让该函数重新工作，行为与从前一样。

<!--
Assuming we did all of that correctly, we got clox back to a runnable
state. Fire it up and it does... exactly what it did before. We haven't added
any new features yet, so this is kind of a let down. But all of the
infrastructure is there and ready for us now. Let's take advantage of it.
-->
假定我们都做对了，clox 又回到可运行状态。启动它，它会……做和从前一模一样的事。我们还没加任何新特性，多少有点扫兴。但基础设施都已就位，等着我们用了。那就用起来吧。

<!--
-- Function Declarations
-->
## 函数声明

<!--
Before we can do call expressions, we need something to call, so we'll do
function declarations first. The <span name="fun">fun</span> starts with a
keyword.
-->
要做调用表达式，得先有东西可调，所以先做函数声明。这<span name="fun">好玩</span>的事从一个关键字开始。

<aside name="fun">

<!--
Yes, I *am* proud of myself for this dumb joke, thank you for asking.
-->
是的，我*确实*为这个蹩脚笑话感到自豪，谢谢你问。

</aside>

^code match-fun (1 before, 1 after)

<!--
That passes control to here:
-->
控制流转到这里：

^code fun-declaration

<!--
Functions are first-class values, and a function declaration simply creates and
stores one in a newly declared variable. So we parse the name just like any
other variable declaration. A function declaration at the top level will bind
the function to a global variable. Inside a block or other function, a function
declaration creates a local variable.
-->
函数是一等值，函数声明只不过创建一个，并把它存进新声明的变量。所以我们像解析其他变量声明一样解析名字。顶层的函数声明把函数绑定到全局变量；在块或其他函数内部，函数声明则创建局部变量。

<!--
In an earlier chapter, I explained how variables [get defined in two
stages][stage]. This ensures you can't access a variable's value inside the
variable's own initializer. That would be bad because the variable doesn't
*have* a value yet.

[stage]: local-variables.html#another-scope-edge-case
-->
在先前的一章，我解释过变量如何[分两阶段定义][stage]。这确保你不能在变量自己的初始化式里访问它的值——那会很糟，因为变量还*没有*值。

[stage]: local-variables.html#another-scope-edge-case

<!--
Functions don't suffer from this problem. It's safe for a function to refer to
its own name inside its body. You can't *call* the function and execute the body
until after it's fully defined, so you'll never see the variable in an
uninitialized state. Practically speaking, it's useful to allow this in order to
support recursive local functions.
-->
函数没有这个问题。函数在自己的函数体里引用自己的名字是安全的。在它完全定义之前，你没法*调用*该函数并执行函数体，因此永远看不到未初始化状态的变量。就实用而言，允许这一点有助于支持递归的局部函数。

<!--
To make that work, we mark the function declaration's variable "initialized" as
soon as we compile the name, before we compile the body. That way the name can
be referenced inside the body without generating an error.
-->
为做到这一点，我们一编译完名字——在编译函数体之前——就把函数声明的变量标记为“已初始化”。这样名字就能在函数体内被引用，而不会产生错误。

<!--
We do need one check, though.
-->
不过我们确实需要一处检查。

^code check-depth (1 before, 1 after)

<!--
Before, we called `markInitialized()` only when we already knew we were in a
local scope. Now, a top-level function declaration will also call this function.
When that happens, there is no local variable to mark initialized -- the
function is bound to a global variable.
-->
从前，我们只在已知处于局部作用域时才调用 `markInitialized()`。如今顶层函数声明也会调用它。那种情况下，没有局部变量可标记为已初始化——函数绑定的是全局变量。

<!--
Next, we compile the function itself -- its parameter list and block body. For
that, we use a separate helper function. That helper generates code that
leaves the resulting function object on top of the stack. After that, we call
`defineVariable()` to store that function back into the variable we declared for
it.
-->
接下来编译函数本身——参数列表和块体。为此我们用一个单独的辅助函数。该辅助函数生成的代码会把得到的函数对象留在栈顶。之后我们调用 `defineVariable()`，把那个函数存回我们为它声明的变量。

<!--
I split out the code to compile the parameters and body because we'll reuse it
later for parsing method declarations inside classes. Let's build it
incrementally, starting with this:
-->
我把编译参数和函数体的代码拆出来，是因为稍后解析类里的方法声明时还会复用它。我们增量构建，从这段开始：

^code compile-function

<aside name="no-end-scope">

<!--
This `beginScope()` doesn't have a corresponding `endScope()` call. Because we
end Compiler completely when we reach the end of the function body, there's no
need to close the lingering outermost scope.
-->
这个 `beginScope()` 没有对应的 `endScope()` 调用。因为到达函数体末尾时我们会彻底结束 Compiler，不必再去关闭那个残留的最外层作用域。

</aside>

<!--
For now, we won't worry about parameters. We parse an empty pair of parentheses
followed by the body. The body starts with a left curly brace, which we parse
here. Then we call our existing `block()` function, which knows how to compile
the rest of a block including the closing brace.
-->
眼下先不管参数。我们解析一对空括号，再跟函数体。函数体以左花括号开头，我们在这里解析它。然后调用已有的 `block()`，它知道如何编译块的其余部分，包括右花括号。

<!--
-- A stack of compilers
-->
### 编译器栈

<!--
The interesting parts are the compiler stuff at the top and bottom. The Compiler
struct stores data like which slots are owned by which local variables, how many
blocks of nesting we're currently in, etc. All of that is specific to a single
function. But now the front end needs to handle compiling multiple functions
<span name="nested">nested</span> within each other.
-->
有意思的部分是顶上和底下那些编译器相关的东西。Compiler 结构体存放诸如哪些槽属于哪些局部变量、当前嵌套了多少层块之类的数据。这一切都针对单个函数。但如今前端需要处理互相<span name="nested">嵌套</span>的多个函数的编译。

<aside name="nested">

<!--
Remember that the compiler treats top-level code as the body of an implicit
function, so as soon as we add *any* function declarations, we're in a world of
nested functions.
-->
别忘了，编译器把顶层代码当作隐式函数的函数体，因此一旦加入*任何*函数声明，我们就进入了嵌套函数的世界。

</aside>

<!--
The trick for managing that is to create a separate Compiler for each function
being compiled. When we start compiling a function declaration, we create a new
Compiler on the C stack and initialize it. `initCompiler()` sets that Compiler
to be the current one. Then, as we compile the body, all of the functions that
emit bytecode write to the chunk owned by the new Compiler's function.
-->
管理这一点的诀窍，是为每个正在编译的函数创建一个单独的 Compiler。开始编译函数声明时，我们在 C 栈上新建一个 Compiler 并初始化。`initCompiler()` 把那个 Compiler 设为当前的。随后编译函数体时，所有发射字节码的函数都写到新 Compiler 的函数所拥有的 chunk 里。

<!--
After we reach the end of the function's block body, we call `endCompiler()`.
That yields the newly compiled function object, which we store as a constant in
the *surrounding* function's constant table. But, wait, how do we get back to
the surrounding function? We lost it when `initCompiler()` overwrote the current
compiler pointer.
-->
到达函数块体的末尾后，我们调用 `endCompiler()`。它产出新编译好的函数对象，我们把它作为常量存进*外围*函数的常量表。可是等等，我们怎么回到外围函数？`initCompiler()` 覆盖当前编译器指针时，我们已经把它弄丢了。

<!--
We fix that by treating the series of nested Compiler structs as a stack. Unlike
the Value and CallFrame stacks in the VM, we won't use an array. Instead, we use
a linked list. Each Compiler points back to the Compiler for the function that
encloses it, all the way back to the root Compiler for the top-level code.
-->
我们的修法是：把这一串嵌套的 Compiler 结构体当作栈。与虚拟机里的 Value 栈和 CallFrame 栈不同，我们不用数组，而用链表。每个 Compiler 回指包围它的那个函数的 Compiler，一路回到顶层代码的根 Compiler。

^code enclosing-field (2 before, 1 after)

<!--
Inside the Compiler struct, we can't reference the Compiler *typedef* since that
declaration hasn't finished yet. Instead, we give a name to the struct itself
and use that for the field's type. C is weird.
-->
在 Compiler 结构体内部，我们不能引用 Compiler *typedef*，因为那个声明还没完成。于是我们给结构体本身起个名字，用它作为字段类型。C 就是这么怪。

<!--
When initializing a new Compiler, we capture the about-to-no-longer-be-current
one in that pointer.
-->
初始化新 Compiler 时，我们把即将不再是当前的那个，抓进那个指针。

^code store-enclosing (1 before, 1 after)

<!--
Then when a Compiler finishes, it pops itself off the stack by restoring the
previous compiler to be the new current one.
-->
然后当一个 Compiler 结束时，它把自己从栈上弹出：把先前的编译器恢复为新的当前编译器。

^code restore-enclosing (2 before, 1 after)

<!--
Note that we don't even need to <span name="compiler">dynamically</span>
allocate the Compiler structs. Each is stored as a local variable in the C stack
-- either in `compile()` or `function()`. The linked list of Compilers threads
through the C stack. The reason we can get an unbounded number of them is
because our compiler uses recursive descent, so `function()` ends up calling
itself recursively when you have nested function declarations.
-->
注意，我们甚至不必<span name="compiler">动态</span>分配 Compiler 结构体。每一个都作为 C 栈上的局部变量存放——要么在 `compile()` 里，要么在 `function()` 里。Compiler 的链表穿行于 C 栈之上。之所以能有无上限的个数，是因为我们的编译器使用递归下降，于是有嵌套函数声明时，`function()` 最终会递归调用自己。

<aside name="compiler">

<!--
Using the native stack for Compiler structs does mean our compiler has a
practical limit on how deeply nested function declarations can be. Go too far
and you could overflow the C stack. If we want the compiler to be more robust
against pathological or even malicious code -- a real concern for tools like
JavaScript VMs -- it would be good to have our compiler artificially limit the
amount of function nesting it permits.
-->
用原生栈存放 Compiler 结构体，意味着我们的编译器对函数声明能嵌套多深有一个实际限制。走得太远，就可能溢出 C 栈。若想让编译器对病态甚至恶意代码更稳健——对 JavaScript 虚拟机这类工具而言，这是真实的关切——最好让编译器人为限制它允许的函数嵌套深度。

</aside>

<!--
-- Function parameters
-->
### 函数参数

<!--
Functions aren't very useful if you can't pass arguments to them, so let's do
parameters next.
-->
若不能传实参，函数就没多大用，所以接下来做参数。

^code parameters (1 before, 1 after)

<!--
Semantically, a parameter is simply a local variable declared in the outermost
lexical scope of the function body. We get to use the existing compiler support
for declaring named local variables to parse and compile parameters. Unlike
local variables, which have initializers, there's no code here to initialize the
parameter's value. We'll see how they are initialized later when we do argument
passing in function calls.
-->
就语义而言，参数不过是在函数体最外层词法作用域里声明的局部变量。我们可以复用已有的、声明具名局部变量的编译器支持，来解析和编译参数。与带初始化式的局部变量不同，这里没有初始化参数值的代码。等我们做函数调用里的实参传递时，再看它们如何被初始化。

<!--
While we're at it, we note the function's arity by counting how many parameters
we parse. The other piece of metadata we store with a function is its name. When
compiling a function declaration, we call `initCompiler()` right after we parse
the function's name. That means we can grab the name right then from the
previous token.
-->
顺便，我们通过统计解析了多少参数来记下函数的 arity。与函数一起存放的另一块元数据是它的名字。编译函数声明时，我们在解析完函数名之后立刻调用 `initCompiler()`。这意味着我们当时就能从前一个 token 抓取名字。

^code init-function-name (1 before, 2 after)

<!--
Note that we're careful to create a copy of the name string. Remember, the
lexeme points directly into the original source code string. That string may get
freed once the code is finished compiling. The function object we create in the
compiler outlives the compiler and persists until runtime. So it needs its own
heap-allocated name string that it can keep around.
-->
注意我们小心地创建了名字字符串的副本。记住，词素直接指向原始源码字符串。那段字符串可能在代码编译完成后就被释放。我们在编译器里创建的函数对象比编译器活得更久，一直持续到运行时。因此它需要自己那份堆上分配的名字字符串，好一直留着。

<!--
Rad. Now we can compile function declarations, like this:
-->
妙。现在我们可以编译函数声明了，比如：

```lox
fun areWeHavingItYet() {
  print "Yes we are!";
}

print areWeHavingItYet;
```

<!--
We just can't do anything <span name="useful">useful</span> with them.
-->
只是还不能拿它们做任何<span name="useful">有用</span>的事。

<aside name="useful">

<!--
We can print them! I guess that's not very useful, though.
-->
我们可以打印它们！不过我想那也没多大用。

</aside>

<!--
-- Function Calls
-->
## 函数调用

<!--
By the end of this section, we'll start to see some interesting behavior. The
next step is calling functions. We don't usually think of it this way, but a
function call expression is kind of an infix `(` operator. You have a
high-precedence expression on the left for the thing being called -- usually
just a single identifier. Then the `(` in the middle, followed by the argument
expressions separated by commas, and a final `)` to wrap it up at the end.
-->
到本节结束，我们会开始看到一些有趣的行为。下一步是调用函数。我们通常不这么想，但函数调用表达式有点像中缀的 `(` 运算符。左边是一个高优先级表达式，表示被调用的东西——通常只是单个标识符。中间是 `(`，后面跟着逗号分隔的实参表达式，最后用 `)` 收尾。

<!--
That odd grammatical perspective explains how to hook the syntax into our
parsing table.
-->
这个古怪的语法视角，解释了如何把该语法挂进我们的解析表。

^code infix-left-paren (1 before, 1 after)

<!--
When the parser encounters a left parenthesis following an expression, it
dispatches to a new parser function.
-->
当解析器在表达式之后遇到左括号时，它分派到一个新的解析函数。

^code compile-call

<!--
We've already consumed the `(` token, so next we compile the arguments using a
separate `argumentList()` helper. That function returns the number of arguments
it compiled. Each argument expression generates code that leaves its value on
the stack in preparation for the call. After that, we emit a new `OP_CALL`
instruction to invoke the function, using the argument count as an operand.
-->
我们已经消费了 `(` token，接下来用单独的 `argumentList()` 辅助函数编译实参。该函数返回它编译了多少个实参。每个实参表达式生成的代码会把其值留在栈上，为调用做准备。之后我们发射一条新的 `OP_CALL` 指令来调用函数，以实参个数作为操作数。

<!--
We compile the arguments using this friend:
-->
我们用这位朋友来编译实参：

^code argument-list

<!--
That code should look familiar from jlox. We chew through arguments as long as
we find commas after each expression. Once we run out, we consume the final
closing parenthesis and we're done.
-->
那段代码在 jlox 里该很眼熟。只要每个表达式后面还有逗号，我们就继续啃实参。啃完后消费最后的右括号，就完事了。

<!--
Well, almost. Back in jlox, we added a compile-time check that you don't pass
more than 255 arguments to a call. At the time, I said that was because clox
would need a similar limit. Now you can see why -- since we stuff the argument
count into the bytecode as a single-byte operand, we can only go up to 255. We
need to verify that in this compiler too.
-->
差不多。早在 jlox 里，我们就加过编译期检查：一次调用不能传超过 255 个实参。当时我说，是因为 clox 也会需要类似限制。现在你能明白为什么了——我们把实参个数作为单字节操作数塞进字节码，最多只能到 255。这个编译器里也要验证这一点。

^code arg-limit (1 before, 1 after)

<!--
That's the front end. Let's skip over to the back end, with a quick stop in the
middle to declare the new instruction.
-->
前端到此为止。我们跳到后端，中途稍停，声明一下新指令。

^code op-call (1 before, 1 after)

<!--
-- Binding arguments to parameters
-->
### 将实参绑定到形参

<!--
Before we get to the implementation, we should think about what the stack looks
like at the point of a call and what we need to do from there. When we reach the
call instruction, we have already executed the expression for the function being
called, followed by its arguments. Say our program looks like this:
-->
动手实现之前，我们应该想想调用那一刻栈长什么样，以及从那儿要做什么。到达调用指令时，我们已经执行了被调用函数的表达式，以及它的各个实参。假设程序是这样：

```lox
fun sum(a, b, c) {
  return a + b + c;
}

print 4 + sum(5, 6, 7);
```

<!--
If we pause the VM right on the `OP_CALL` instruction for that call to `sum()`,
the stack looks like this:
-->
若在对 `sum()` 那次调用的 `OP_CALL` 指令上暂停虚拟机，栈看起来像这样：

<img src="image/calls-and-functions/argument-stack.png" alt="Stack: 4, fn sum, 5, 6, 7." />

<!--
Picture this from the perspective of `sum()` itself. When the compiler compiled
`sum()`, it automatically allocated slot zero. Then, after that, it allocated
local slots for the parameters `a`, `b`, and `c`, in order. To perform a call to
`sum()`, we need a CallFrame initialized with the function being called and a
region of stack slots that it can use. Then we need to collect the arguments
passed to the function and get them into the corresponding slots for the
parameters.
-->
从 `sum()` 自身的视角来看。编译器编译 `sum()` 时，自动分配了槽零。之后按顺序为参数 `a`、`b`、`c` 分配局部槽。要对 `sum()` 发起调用，我们需要一个用被调用函数初始化好的 CallFrame，以及它可用的一段栈槽区域。然后还得把传入的实参收集起来，放进对应的形参槽。

<!--
When the VM starts executing the body of `sum()`, we want its stack window to
look like this:
-->
当虚拟机开始执行 `sum()` 的函数体时，我们希望它的栈窗口长这样：

<img src="image/calls-and-functions/parameter-window.png" alt="The same stack with the sum() function's call frame window surrounding fn sum, 5, 6, and 7." />

<!--
Do you notice how the argument slots that the caller sets up and the parameter
slots the callee needs are both in exactly the right order? How convenient! This
is no coincidence. When I talked about each CallFrame having its own window into
the stack, I never said those windows must be *disjoint*. There's nothing
preventing us from overlapping them, like this:
-->
注意到了吗：调用者准备好的实参槽，与被调用者需要的形参槽，顺序恰好完全一致？多方便！这并非巧合。我谈到每个 CallFrame 在栈上各有一扇窗口时，从未说过那些窗口必须*互不相交*。没什么阻止我们让它们重叠，像这样：

<img src="image/calls-and-functions/overlapping-windows.png" alt="The same stack with the top-level call frame covering the entire stack and the sum() function's call frame window surrounding fn sum, 5, 6, and 7." />

<!--
<span name="lua">The</span> top of the caller's stack contains the function
being called followed by the arguments in order. We know the caller doesn't have
any other slots above those in use because any temporaries needed when
evaluating argument expressions have been discarded by now. The bottom of the
callee's stack overlaps so that the parameter slots exactly line up with where
the argument values already live.
-->
<span name="lua">调用者</span>栈的顶部装着被调用的函数，后面按顺序跟着实参。我们知道调用者在这些之上没有别的在用槽，因为求值实参表达式时需要的临时值到此刻都已丢弃。被调用者栈的底部与之重叠，好让形参槽恰好对齐实参值已经所在的位置。

<aside name="lua">

<!--
Different bytecode VMs and real CPU architectures have different *calling
conventions*, which is the specific mechanism they use to pass arguments, store
the return address, etc. The mechanism I use here is based on Lua's clean, fast
virtual machine.
-->
不同的字节码虚拟机和真实 CPU 架构有不同的*调用约定*——即它们传递实参、存放返回地址等所用的具体机制。我这里用的机制，基于 Lua 那干净、快速的虚拟机。

</aside>

<!--
This means that we don't need to do *any* work to "bind an argument to a
parameter". There's no copying values between slots or across environments. The
arguments are already exactly where they need to be. It's hard to beat that for
performance.
-->
这意味着我们不必做*任何*“把实参绑定到形参”的工作。没有在槽之间或跨环境拷贝值。实参已经恰好在它们该在的地方。论性能，很难再比这更好了。

<!--
Time to implement the call instruction.
-->
该实现调用指令了。

^code interpret-call (1 before, 1 after)

<!--
We need to know the function being called and the number of arguments passed to
it. We get the latter from the instruction's operand. That also tells us where
to find the function on the stack by counting past the argument slots from the
top of the stack. We hand that data off to a separate `callValue()` function. If
that returns `false`, it means the call caused some sort of runtime error. When
that happens, we abort the interpreter.
-->
我们需要知道被调用的函数，以及传给它的实参个数。后者来自指令的操作数。它也告诉我们如何从栈顶往下数过实参槽，找到栈上的函数。我们把这些数据交给单独的 `callValue()`。若它返回 `false`，说明调用引发了某种运行时错误。此时我们中止解释器。

<!--
If `callValue()` is successful, there will be a new frame on the CallFrame stack
for the called function. The `run()` function has its own cached pointer to the
current frame, so we need to update that.
-->
若 `callValue()` 成功，CallFrame 栈上会有一个给被调函数的新帧。`run()` 函数有自己缓存的当前帧指针，所以我们需要更新它。

^code update-frame-after-call (2 before, 1 after)

<!--
Since the bytecode dispatch loop reads from that `frame` variable, when the VM
goes to execute the next instruction, it will read the `ip` from the newly
called function's CallFrame and jump to its code. The work for executing that
call begins here:
-->
由于字节码分派循环从那个 `frame` 变量读取，当虚拟机去执行下一条指令时，它会从新调用的函数的 CallFrame 读取 `ip`，并跳到它的代码。执行那次调用的工作从这里开始：

^code call-value

<aside name="switch">

<!--
Using a `switch` statement to check a single type is overkill now, but will make
sense when we add cases to handle other callable types.
-->
用 `switch` 来检查单一类型眼下有点杀鸡用牛刀，但等我们加上处理其他可调用类型的分支时，就会说得通。

</aside>

<!--
There's more going on here than just initializing a new CallFrame. Because Lox
is dynamically typed, there's nothing to prevent a user from writing bad code
like:
-->
这里发生的不只是初始化一个新 CallFrame。因为 Lox 是动态类型的，没什么能阻止用户写出这种糟糕代码：

```lox
var notAFunction = 123;
notAFunction();
```

<!--
If that happens, the runtime needs to safely report an error and halt. So the
first thing we do is check the type of the value that we're trying to call. If
it's not a function, we error out. Otherwise, the actual call happens here:
-->
若发生这种事，运行时需要安全地报告错误并停下。所以我们先做的第一件事，是检查试图调用的那个值的类型。若不是函数，就报错退出。否则，真正的调用发生在这里：

^code call

<!--
This simply initializes the next CallFrame on the stack. It stores a pointer to
the function being called and points the frame's `ip` to the beginning of the
function's bytecode. Finally, it sets up the `slots` pointer to give the frame
its window into the stack. The arithmetic there ensures that the arguments
already on the stack line up with the function's parameters:
-->
这只是初始化栈上下一个 CallFrame。它存下指向被调函数的指针，把帧的 `ip` 指向函数字节码的开头。最后设置 `slots` 指针，给帧一扇通往栈的窗口。那里的算术确保栈上已有的实参与函数的形参对齐：

<img src="image/calls-and-functions/arithmetic.png" alt="The arithmetic to calculate frame-&gt;slots from stackTop and argCount." />

<!--
The funny little `- 1` is to account for stack slot zero which the compiler set
aside for when we add methods later. The parameters start at slot one so we
make the window start one slot earlier to align them with the arguments.
-->
那个有趣的小小 `- 1`，是为了照顾编译器为日后加入方法而预留的栈槽零。参数从槽一开始，所以我们让窗口提前一个槽开始，好让它们与实参对齐。

<!--
Before we move on, let's add the new instruction to our disassembler.
-->
继续之前，先把新指令加进反汇编器。

^code disassemble-call (1 before, 1 after)

<!--
And one more quick side trip. Now that we have a handy function for initiating a
CallFrame, we may as well use it to set up the first frame for executing the
top-level code.
-->
再做一个小小的旁支。既然我们有了发起 CallFrame 的便利函数，不妨也用它来为执行顶层代码设置第一帧。

^code interpret (1 before, 2 after)

<!--
OK, now back to calls...
-->
好，现在回到调用……

<!--
-- Runtime error checking
-->
### 运行时错误检查

<!--
The overlapping stack windows work based on the assumption that a call passes
exactly one argument for each of the function's parameters. But, again, because
Lox ain't statically typed, a foolish user could pass too many or too few
arguments. In Lox, we've defined that to be a runtime error, which we report
like so:
-->
重叠的栈窗口基于这样一个假设：一次调用为函数的每个形参恰好传一个实参。但同样，因为 Lox 不是静态类型的，愚蠢的用户可能传太多或太少。在 Lox 里，我们把这定义为运行时错误，报告方式如下：

^code check-arity (1 before, 1 after)

<!--
Pretty straightforward. This is why we store the arity of each function inside
the ObjFunction for it.
-->
相当直截了当。这就是我们把每个函数的 arity 存在对应 ObjFunction 里的原因。

<!--
There's another error we need to report that's less to do with the user's
foolishness than our own. Because the CallFrame array has a fixed size, we need
to ensure a deep call chain doesn't overflow it.
-->
还有一个错误需要报告，与其说关乎用户的愚蠢，不如说关乎我们自己的局限。因为 CallFrame 数组大小固定，我们得确保很深的调用链不会溢出它。

^code check-overflow (2 before, 1 after)

<!--
In practice, if a program gets anywhere close to this limit, there's most likely
a bug in some runaway recursive code.
-->
实践中，若程序接近这个上限，多半是某段失控的递归代码里有 bug。

<!--
-- Printing stack traces
-->
### 打印栈回溯

<!--
While we're on the subject of runtime errors, let's spend a little time making
them more useful. Stopping on a runtime error is important to prevent the VM
from crashing and burning in some ill-defined way. But simply aborting doesn't
help the user fix their code that *caused* that error.
-->
既然说到运行时错误，不妨花点时间让它们更有用。在运行时错误上停下很重要，以免虚拟机以某种说不清的方式崩溃焚毁。但单纯中止并不能帮用户修好*导致*该错误的代码。

<!--
The classic tool to aid debugging runtime failures is a **stack trace** -- a
print out of each function that was still executing when the program died, and
where the execution was at the point that it died. Now that we have a call stack
and we've conveniently stored each function's name, we can show that entire
stack when a runtime error disrupts the harmony of the user's existence. It
looks like this:
-->
辅助调试运行时失败的经典工具是**栈回溯**——打印出程序死去时仍在执行的每个函数，以及死去那一刻执行到了哪里。如今我们有了调用栈，又方便地存下了每个函数的名字，当运行时错误搅乱用户存在的和谐时，我们就能展示整条栈。它看起来像这样：

^code runtime-error-stack (2 before, 2 after)

<aside name="minus">

<!--
The `- 1` is because the IP is already sitting on the next instruction to be
executed but we want the stack trace to point to the previous failed
instruction.
-->
那个 `- 1` 是因为 IP 已经停在下一条待执行指令上，而我们希望栈回溯指向先前那条失败的指令。

</aside>

<!--
After printing the error message itself, we walk the call stack from <span
name="top">top</span> (the most recently called function) to bottom (the
top-level code). For each frame, we find the line number that corresponds to the
current `ip` inside that frame's function. Then we print that line number along
with the function name.
-->
打印完错误消息本身后，我们从<span name="top">顶</span>（最近调用的函数）走到底（顶层代码）遍历调用栈。对每一帧，我们找出对应该帧函数内当前 `ip` 的行号，然后连同函数名一起打印。

<aside name="top">

<!--
There is some disagreement on which order stack frames should be shown in a
trace. Most put the innermost function as the first line and work their way
towards the bottom of the stack. Python prints them out in the opposite order.
So reading from top to bottom tells you how your program got to where it is, and
the last line is where the error actually occurred.

There's a logic to that style. It ensures you can always see the innermost
function even if the stack trace is too long to fit on one screen. On the other
hand, the "[inverted pyramid][]" from journalism tells us we should put the most
important information *first* in a block of text. In a stack trace, that's the
function where the error actually occurred. Most other language implementations
do that.

[inverted pyramid]: https://en.wikipedia.org/wiki/Inverted_pyramid_(journalism)
-->
栈帧在回溯里应按何种顺序显示，存在一些分歧。大多数把最内层函数放在第一行，再朝栈底走。Python 以相反顺序打印。于是从上往下读，能看出程序如何到达当前位置，最后一行才是错误实际发生处。

那种风格有其道理：即便栈回溯长得一屏装不下，你也总能看见最内层函数。另一方面，新闻学里的“[倒金字塔][inverted pyramid]”告诉我们，一块文字里最重要的信息应放在*最前*。在栈回溯里，那就是错误实际发生的函数。大多数其他语言实现都这么做。

[inverted pyramid]: https://en.wikipedia.org/wiki/Inverted_pyramid_(journalism)

</aside>

<!--
For example, if you run this broken program:
-->
例如，若你运行这个坏掉的程序：

```lox
fun a() { b(); }
fun b() { c(); }
fun c() {
  c("too", "many");
}

a();
```

<!--
It prints out:
-->
它会打印：

```text
Expected 0 arguments but got 2.
[line 4] in c()
[line 2] in b()
[line 1] in a()
[line 7] in script
```

<!--
That doesn't look too bad, does it?
-->
看起来还不赖，对吧？

<!--
-- Returning from functions
-->
### 从函数返回

<!--
We're getting close. We can call functions, and the VM will execute them. But we
can't *return* from them yet. We've had an `OP_RETURN` instruction for quite
some time, but it's always had some kind of temporary code hanging out in it
just to get us out of the bytecode loop. The time has arrived for a real
implementation.
-->
我们接近了。我们可以调用函数，虚拟机也会执行它们。但还不能从它们*返回*。我们早就有了 `OP_RETURN` 指令，可里面一直挂着某种临时代码，只为让我们跳出字节码循环。真正实现的时候到了。

^code interpret-return (1 before, 1 after)

<!--
When a function returns a value, that value will be on top of the stack. We're
about to discard the called function's entire stack window, so we pop that
return value off and hang on to it. Then we discard the CallFrame for the
returning function. If that was the very last CallFrame, it means we've finished
executing the top-level code. The entire program is done, so we pop the main
script function from the stack and then exit the interpreter.
-->
函数返回一个值时，该值会在栈顶。我们即将丢弃被调函数的整个栈窗口，所以先把返回值弹出并抓紧。然后丢弃返回函数的 CallFrame。若那是最后一个 CallFrame，说明顶层代码已执行完。整个程序结束了，于是我们从栈上弹出主脚本函数，然后退出解释器。

<!--
Otherwise, we discard all of the slots the callee was using for its parameters
and local variables. That includes the same slots the caller used to pass the
arguments. Now that the call is done, the caller doesn't need them anymore. This
means the top of the stack ends up right at the beginning of the returning
function's stack window.
-->
否则，我们丢弃被调用者用于形参和局部变量的全部槽。这包括调用者用来传递实参的那些槽。调用既已完成，调用者不再需要它们。这意味着栈顶最终恰好落在返回函数的栈窗口起点。

<!--
We push the return value back onto the stack at that new, lower location. Then
we update the `run()` function's cached pointer to the current frame. Just like
when we began a call, on the next iteration of the bytecode dispatch loop, the
VM will read `ip` from that frame, and execution will jump back to the caller,
right where it left off, immediately after the `OP_CALL` instruction.
-->
我们把返回值推回栈上那个新的、更低的位置。然后更新 `run()` 函数缓存的当前帧指针。就像开始一次调用时那样，在字节码分派循环的下一轮迭代，虚拟机会从该帧读取 `ip`，执行会跳回调用者——正好停在离开之处，紧挨在 `OP_CALL` 指令之后。

<img src="image/calls-and-functions/return.png" alt="Each step of the return process: popping the return value, discarding the call frame, pushing the return value." />

<!--
Note that we assume here that the function *did* actually return a value, but
a function can implicitly return by reaching the end of its body:
-->
注意我们这里假定函数*确实*返回了一个值，但函数也可以通过到达函数体末尾而隐式返回：

```lox
fun noReturn() {
  print "Do stuff";
  // No return here.
}

print noReturn(); // ???
```

<!--
We need to handle that correctly too. The language is specified to implicitly
return `nil` in that case. To make that happen, we add this:
-->
我们也得正确处理那种情况。语言规定此时隐式返回 `nil`。为此我们加上这段：

^code return-nil (1 before, 2 after)

<!--
The compiler calls `emitReturn()` to write the `OP_RETURN` instruction at the
end of a function body. Now, before that, it emits an instruction to push `nil`
onto the stack. And with that, we have working function calls! They can even
take parameters! It almost looks like we know what we're doing here.
-->
编译器调用 `emitReturn()`，在函数体末尾写入 `OP_RETURN` 指令。如今在那之前，它会先发射一条把 `nil` 压栈的指令。至此，我们有了能工作的函数调用！它们甚至还能带参数！看起来我们几乎像是知道自己在干什么。

<!--
-- Return Statements
-->
## return 语句

<!--
If you want a function that returns something other than the implicit `nil`, you
need a `return` statement. Let's get that working.
-->
若想要一个返回值不是隐式 `nil` 的函数，就需要 `return` 语句。让我们把它做起来。

^code match-return (1 before, 1 after)

<!--
When the compiler sees a `return` keyword, it goes here:
-->
编译器看到 `return` 关键字时，转到这里：

^code return-statement

<!--
The return value expression is optional, so the parser looks for a semicolon
token to tell if a value was provided. If there is no return value, the
statement implicitly returns `nil`. We implement that by calling `emitReturn()`,
which emits an `OP_NIL` instruction. Otherwise, we compile the return value
expression and return it with an `OP_RETURN` instruction.
-->
返回值表达式是可选的，所以解析器通过寻找分号 token 来判断是否提供了值。若没有返回值，语句隐式返回 `nil`。我们通过调用 `emitReturn()` 实现——它会发射一条 `OP_NIL`。否则，我们编译返回值表达式，并用 `OP_RETURN` 返回它。

<!--
This is the same `OP_RETURN` instruction we've already implemented -- we don't
need any new runtime code. This is quite a difference from jlox. There, we had
to use exceptions to unwind the stack when a `return` statement was executed.
That was because you could return from deep inside some nested blocks. Since
jlox recursively walks the AST, that meant there were a bunch of Java method
calls we needed to escape out of.
-->
这就是我们已经实现过的那条 `OP_RETURN`——不需要任何新的运行时代码。这与 jlox 大不相同。在那边，执行 `return` 时我们得用异常来展开栈。因为你可以从嵌套很深的块里返回；而 jlox 递归遍历 AST，意味着有一堆 Java 方法调用需要逃出去。

<!--
Our bytecode compiler flattens that all out. We do recursive descent during
parsing, but at runtime, the VM's bytecode dispatch loop is completely flat.
There is no recursion going on at the C level at all. So returning, even from
within some nested blocks, is as straightforward as returning from the end of
the function's body.
-->
我们的字节码编译器把这一切都拍平了。解析时我们做递归下降，但运行时虚拟机的字节码分派循环完全是扁平的。在 C 层面根本没有递归。因此即便从某些嵌套块里返回，也和从函数体末尾返回一样直截了当。

<!--
We're not totally done, though. The new `return` statement gives us a new
compile error to worry about. Returns are useful for returning from functions
but the top level of a Lox program is imperative code too. You shouldn't be able
to <span name="worst">return</span> from there.
-->
不过我们还没完全做完。新的 `return` 语句带来一个新的编译错误需要操心。`return` 对从函数返回很有用，但 Lox 程序的顶层也是命令式代码。你不该能从那里<span name="worst">返回</span>。

```lox
return "What?!";
```

<aside name="worst">

<!--
Allowing `return` at the top level isn't the worst idea in the world. It would
give you a natural way to terminate a script early. You could maybe even use a
returned number to indicate the process's exit code.
-->
允许在顶层 `return` 也不是世上最糟的主意。它会给你一种自然地提前终止脚本的方式。或许甚至还能用返回的数字表示进程的退出码。

</aside>

<!--
We've specified that it's a compile error to have a `return` statement outside
of any function, which we implement like so:
-->
我们已经规定：在任何函数之外出现 `return` 语句是编译错误，实现如下：

^code return-from-script (1 before, 1 after)

<!--
This is one of the reasons we added that FunctionType enum to the compiler.
-->
这正是我们给编译器加上 FunctionType 枚举的原因之一。

<!--
-- Native Functions
-->
## 原生函数

<!--
Our VM is getting more powerful. We've got functions, calls, parameters,
returns. You can define lots of different functions that can call each other in
interesting ways. But, ultimately, they can't really *do* anything. The only
user-visible thing a Lox program can do, regardless of its complexity, is print.
To add more capabilities, we need to expose them to the user.
-->
我们的虚拟机正变得更强大。我们有了函数、调用、参数、返回。你可以定义许多不同的函数，以有趣的方式互相调用。但归根结底，它们并不能真正*做*什么。无论多复杂，Lox 程序唯一对用户可见的事就是打印。要增加更多能力，就得把它们暴露给用户。

<!--
A programming language implementation reaches out and touches the material world
through **native functions**. If you want to be able to write programs that
check the time, read user input, or access the file system, we need to add
native functions -- callable from Lox but implemented in C -- that expose those
capabilities.
-->
编程语言实现经由**原生函数**伸出手去触碰物质世界。若想写出能查看时间、读取用户输入或访问文件系统的程序，就需要加入原生函数——可从 Lox 调用、却在 C 里实现——来暴露这些能力。

<!--
At the language level, Lox is fairly complete -- it's got closures, classes,
inheritance, and other fun stuff. One reason it feels like a toy language is
because it has almost no native capabilities. We could turn it into a real
language by adding a long list of them.
-->
在语言层面，Lox 相当完整——有闭包、类、继承以及其他好玩的东西。它感觉像玩具语言的一个原因，是几乎没有原生能力。加一长串原生函数，就能把它变成一门真正的语言。

<!--
However, grinding through a pile of OS operations isn't actually very
educational. Once you've seen how to bind one piece of C code to Lox, you get
the idea. But you do need to see *one*, and even a single native function
requires us to build out all the machinery for interfacing Lox with C. So we'll
go through that and do all the hard work. Then, when that's done, we'll add one
tiny native function just to prove that it works.
-->
不过，啃一堆操作系统操作其实没多大教育意义。一旦见过如何把一段 C 代码绑定到 Lox，你就懂了。但你确实需要见*一个*；即便单个原生函数，也要求我们搭好 Lox 与 C 对接的全部机制。所以我们会走完那条路，把苦活干完。做完之后，再加一个小小的原生函数，只为证明它能工作。

<!--
The reason we need new machinery is because, from the implementation's
perspective, native functions are different from Lox functions. When they are
called, they don't push a CallFrame, because there's no bytecode code for that
frame to point to. They have no bytecode chunk. Instead, they somehow reference
a piece of native C code.
-->
我们需要新机制的原因是：从实现角度看，原生函数不同于 Lox 函数。它们被调用时不推 CallFrame，因为没有字节码可供那帧指向。它们没有字节码 chunk。相反，它们以某种方式引用一段原生 C 代码。

<!--
We handle this in clox by defining native functions as an entirely different
object type.
-->
在 clox 里，我们把原生函数定义为一种完全不同的对象类型来处理。

^code obj-native (1 before, 2 after)

<!--
The representation is simpler than ObjFunction -- merely an Obj header and a
pointer to the C function that implements the native behavior. The native
function takes the argument count and a pointer to the first argument on the
stack. It accesses the arguments through that pointer. Once it's done, it
returns the result value.
-->
表示比 ObjFunction 更简单——只是一个 Obj 头，外加指向实现原生行为的 C 函数的指针。原生函数接收实参个数，以及指向栈上第一个实参的指针。它通过该指针访问实参。做完后返回结果值。

<!--
As always, a new object type carries some accoutrements with it. To create an
ObjNative, we declare a constructor-like function.
-->
一如既往，新对象类型带着一些配套行头。要创建 ObjNative，我们声明一个类似构造函数的函数。

^code new-native-h (1 before, 1 after)

<!--
We implement that like so:
-->
实现如下：

^code new-native

<!--
The constructor takes a C function pointer to wrap in an ObjNative. It sets up
the object header and stores the function. For the header, we need a new object
type.
-->
构造函数接收一个要包进 ObjNative 的 C 函数指针。它设置对象头并存储该函数。对头而言，我们需要一个新的对象类型。

^code obj-type-native (2 before, 2 after)

<!--
The VM also needs to know how to deallocate a native function object.
-->
虚拟机还需要知道如何释放原生函数对象。

^code free-native (1 before, 1 after)

<!--
There isn't much here since ObjNative doesn't own any extra memory. The other
capability all Lox objects support is being printed.
-->
这里没多少东西，因为 ObjNative 不拥有额外内存。所有 Lox 对象支持的另一项能力是被打印。

^code print-native (1 before, 1 after)

<!--
In order to support dynamic typing, we have a macro to see if a value is a
native function.
-->
为支持动态类型，我们有一条宏来查看一个值是否是原生函数。

^code is-native (1 before, 1 after)

<!--
Assuming that returns true, this macro extracts the C function pointer from a
Value representing a native function:
-->
若它返回真，这条宏从表示原生函数的 Value 中提取 C 函数指针：

^code as-native (1 before, 1 after)

<!--
All of this baggage lets the VM treat native functions like any other object.
You can store them in variables, pass them around, throw them birthday parties,
etc. Of course, the operation we actually care about is *calling* them -- using
one as the left-hand operand in a call expression.
-->
这些行头让虚拟机能把原生函数当作其他任何对象来对待。你可以存进变量、传来传去、给它们办生日派对，等等。当然，我们真正关心的操作是*调用*它们——在调用表达式里把其中一个当作左操作数。

<!--
Over in `callValue()` we add another type case.
-->
在 `callValue()` 里我们再加一个类型分支。

^code call-native (2 before, 1 after)

<!--
If the object being called is a native function, we invoke the C function right
then and there. There's no need to muck with CallFrames or anything. We just
hand off to C, get the result, and stuff it back in the stack. This makes native
functions as fast as we can get.
-->
若被调用的对象是原生函数，我们当场调用那个 C 函数。不必折腾 CallFrame 之类的东西。我们只是交给 C，拿到结果，塞回栈上。这让原生函数尽可能快。

<!--
With this, users should be able to call native functions, but there aren't any
to call. Without something like a foreign function interface, users can't define
their own native functions. That's our job as VM implementers. We'll start with
a helper to define a new native function exposed to Lox programs.
-->
有了这个，用户应该能调用原生函数了，可是还没有可调的。若没有类似外部函数接口的东西，用户无法定义自己的原生函数。那是我们作为虚拟机实现者的工作。我们先从一个辅助函数开始：定义一个暴露给 Lox 程序的新原生函数。

^code define-native

<!--
It takes a pointer to a C function and the name it will be known as in Lox.
We wrap the function in an ObjNative and then store that in a global variable
with the given name.
-->
它接收指向 C 函数的指针，以及该函数在 Lox 里为人知晓的名字。我们把函数包进 ObjNative，再存进给定名字的全局变量。

<!--
You're probably wondering why we push and pop the name and function on the
stack. That looks weird, right? This is the kind of stuff you have to worry
about when <span name="worry">garbage</span> collection gets involved. Both
`copyString()` and `newNative()` dynamically allocate memory. That means once we
have a GC, they can potentially trigger a collection. If that happens, we need
to ensure the collector knows we're not done with the name and ObjFunction so
that it doesn't free them out from under us. Storing them on the value stack
accomplishes that.
-->
你大概在好奇，为何我们要把名字和函数在栈上推入再弹出。看起来挺怪，对吧？一旦<span name="worry">垃圾</span>收集掺和进来，这类事就得操心。`copyString()` 和 `newNative()` 都会动态分配内存。意味着一旦有了 GC，它们可能触发一次收集。若发生那种事，我们得确保收集器知道我们还没用完名字和 ObjFunction，免得它从我们脚下把它们释放掉。把它们存在值栈上就能做到这一点。

<aside name="worry">

<!--
Don't worry if you didn't follow all that. It will make a lot more sense once we
get around to [implementing the GC][gc].

[gc]: garbage-collection.html
-->
若没全跟上，别担心。等我们动手[实现 GC][gc] 时，会清楚得多。

[gc]: garbage-collection.html

</aside>

<!--
It feels silly, but after all of that work, we're going to add only one
little native function.
-->
感觉有点傻，但干完所有这些活之后，我们只加一个小小的原生函数。

^code clock-native

<!--
This returns the elapsed time since the program started running, in seconds. It's
handy for benchmarking Lox programs. In Lox, we'll name it `clock()`.
-->
它返回自程序开始运行以来经过的时间，以秒计。对基准测试 Lox 程序很方便。在 Lox 里，我们把它叫做 `clock()`。

^code define-native-clock (1 before, 1 after)

<!--
To get to the C standard library `clock()` function, the "vm" module needs an
include.
-->
要访问 C 标准库的 `clock()` 函数，“vm” 模块需要一条 include。

^code vm-include-time (1 before, 2 after)

<!--
That was a lot of material to work through, but we did it! Type this in and try
it out:
-->
要啃的材料不少，但我们做到了！输入这段试试看：

```lox
fun fib(n) {
  if (n < 2) return n;
  return fib(n - 2) + fib(n - 1);
}

var start = clock();
print fib(35);
print clock() - start;
```

<!--
We can write a really inefficient recursive Fibonacci function. Even better, we
can measure just <span name="faster">*how*</span> inefficient it is. This is, of
course, not the smartest way to calculate a Fibonacci number. But it is a good
way to stress test a language implementation's support for function calls. On my
machine, running this in clox is about five times faster than in jlox. That's
quite an improvement.
-->
我们可以写一个真正低效的递归斐波那契函数。更妙的是，我们还能测出它到底<span name="faster">*有多*</span>低效。当然，这不是计算斐波那契数最聪明的办法。但它是压力测试一门语言实现对函数调用支持的好方法。在我的机器上，这段在 clox 里跑大约比 jlox 快五倍。相当可观的进步。

<aside name="faster">

<!--
It's a little slower than a comparable Ruby program run in Ruby 2.4.3p205, and
about 3x faster than one run in Python 3.7.3. And we still have a lot of simple
optimizations we can do in our VM.
-->
它比用 Ruby 2.4.3p205 跑的可比 Ruby 程序稍慢一点，比用 Python 3.7.3 跑的大约快 3 倍。而我们虚拟机里还有许多简单优化可以做。

</aside>

<div class="challenges">

<!--
## Challenges
-->
## 挑战

<!--
1.  Reading and writing the `ip` field is one of the most frequent operations
    inside the bytecode loop. Right now, we access it through a pointer to the
    current CallFrame. That requires a pointer indirection which may force the
    CPU to bypass the cache and hit main memory. That can be a real performance
    sink.

    Ideally, we'd keep the `ip` in a native CPU register. C doesn't let us
    *require* that without dropping into inline assembly, but we can structure
    the code to encourage the compiler to make that optimization. If we store
    the `ip` directly in a C local variable and mark it `register`, there's a
    good chance the C compiler will accede to our polite request.

    This does mean we need to be careful to load and store the local `ip` back
    into the correct CallFrame when starting and ending function calls.
    Implement this optimization. Write a couple of benchmarks and see how it
    affects the performance. Do you think the extra code complexity is worth it?
-->
1.  读写 `ip` 字段是字节码循环里最频繁的操作之一。眼下我们通过指向当前 CallFrame 的指针访问它。这需要一次指针间接，可能迫使 CPU 绕过缓存去撞主存。那可以是真正的性能黑洞。

    理想情况下，我们想把 `ip` 留在原生 CPU 寄存器里。若不掉进内联汇编，C 不让我们*强制*要求这一点，但我们可以组织代码，鼓励编译器做那项优化。若把 `ip` 直接存在 C 局部变量里并标上 `register`，C 编译器很有机会答应我们这个客气的请求。

    这意味着在开始和结束函数调用时，我们得小心把局部 `ip` 加载并写回正确的 CallFrame。实现这项优化。写几个基准测试，看看它对性能有何影响。你认为额外的代码复杂度值得吗？

<!--
2.  Native function calls are fast in part because we don't validate that the
    call passes as many arguments as the function expects. We really should, or
    an incorrect call to a native function without enough arguments could cause
    the function to read uninitialized memory. Add arity checking.
-->
2.  原生函数调用之所以快，部分原因是我们不验证调用是否传了函数期望个数的实参。我们其实应该验证——否则对原生函数的错误调用若实参不足，可能导致函数读取未初始化内存。加上 arity 检查。

<!--
3.  Right now, there's no way for a native function to signal a runtime error.
    In a real implementation, this is something we'd need to support because
    native functions live in the statically typed world of C but are called
    from dynamically typed Lox land. If a user, say, tries to pass a string to
    `sqrt()`, that native function needs to report a runtime error.

    Extend the native function system to support that. How does this capability
    affect the performance of native calls?
-->
3.  眼下，原生函数没有办法发出运行时错误信号。在真正的实现里，我们需要支持这一点，因为原生函数生活在 C 的静态类型世界里，却从动态类型的 Lox 国度被调用。比方说，若用户试图把字符串传给 `sqrt()`，那个原生函数需要报告运行时错误。

    扩展原生函数系统以支持这一点。这项能力如何影响原生调用的性能？

<!--
4.  Add some more native functions to do things you find useful. Write some
    programs using those. What did you add? How do they affect the feel of the
    language and how practical it is?
-->
4.  再加一些你觉得有用的原生函数。写几个用到它们的程序。你加了什么？它们如何影响语言的手感，以及它有多实用？

</div>
