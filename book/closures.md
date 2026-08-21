# 闭包

<!--
> As the man said, for every complex problem there's a simple solution, and it's
> wrong.
>
> <cite>Umberto Eco, <em>Foucault's Pendulum</em></cite>
-->
> 正如那人所说，每个复杂问题都有一个简单的解法——而且是错的。
>
> <cite>翁贝托·埃科，<em>《傅科摆》</em></cite>

<!--
Thanks to our diligent labor in [the last chapter][last], we have a virtual
machine with working functions. What it lacks is closures. Aside from global
variables, which are their own breed of animal, a function has no way to
reference a variable declared outside of its own body.
-->
多亏[上一章][last]的辛勤劳作，我们已有一台能跑函数的虚拟机。它所缺的，是闭包。除了全局变量——那是另一路物种——函数没法引用声明在自身函数体之外的变量。

[last]: calls-and-functions.html

```lox
var x = "global";
fun outer() {
  var x = "outer";
  fun inner() {
    print x;
  }
  inner();
}
outer();
```

<!--
Run this example now and it prints "global". It's supposed to print "outer". To
fix this, we need to include the entire lexical scope of all surrounding
functions when resolving a variable.
-->
现在跑这个例子，打出来的是 `"global"`。它本该打印 `"outer"`。要修好这一点，解析变量时就必须把所有外围函数的整个词法作用域一并纳入。

<!--
This problem is harder in clox than it was in jlox because our bytecode VM
stores locals on a stack. We used a stack because I claimed locals have stack
semantics -- variables are discarded in the reverse order that they are created.
But with closures, that's only *mostly* true.
-->
这个问题在 clox 里比在 jlox 里更棘手，因为我们的字节码虚拟机把局部变量放在栈上。我们用栈，是因为我声称局部变量具有栈语义——变量按创建的相反顺序被丢弃。但有了闭包，这话就只是*大体*成立。

```lox
fun makeClosure() {
  var local = "local";
  fun closure() {
    print local;
  }
  return closure;
}

var closure = makeClosure();
closure();
```

<!--
The outer function `makeClosure()` declares a variable, `local`. It also creates
an inner function, `closure()` that captures that variable. Then `makeClosure()`
returns a reference to that function. Since the closure <span
name="flying">escapes</span> while holding on to the local variable, `local` must
outlive the function call where it was created.
-->
外层函数 `makeClosure()` 声明了变量 `local`。它还创建了内层函数 `closure()`，后者捕获了那个变量。然后 `makeClosure()` 返回对该函数的引用。既然闭包在攥着局部变量的同时<span name="flying">逃逸</span>了出去，`local` 就必须比创建它的那次函数调用活得更久。

<aside name="flying">

<img src="image/closures/flying.png" class="above" alt="A local variable flying away from the stack."/>

<!--
Oh no, it's escaping!
-->
糟了，它要逃了！

</aside>

<!--
We could solve this problem by dynamically allocating memory for all local
variables. That's what jlox does by putting everything in those Environment
objects that float around in Java's heap. But we don't want to. Using a <span
name="stack">stack</span> is *really* fast. Most local variables are *not*
captured by closures and do have stack semantics. It would suck to make all of
those slower for the benefit of the rare local that is captured.
-->
我们可以给所有局部变量动态分配内存来解决这问题——jlox 就是这么干的，把一切都塞进那些漂在 Java 堆上的 Environment 对象里。但我们不想这么做。用<span name="stack">栈</span>真的*非常*快。大多数局部变量*并不*被闭包捕获，而且确实具有栈语义。为了那少数被捕获的局部变量，把全部局部变量都拖慢，实在太亏了。

<aside name="stack">

<!--
There is a reason that C and Java use the stack for their local variables, after
all.
-->
毕竟，C 和 Java 把局部变量放在栈上，不是没有道理的。

</aside>

<!--
This means a more complex approach than we used in our Java interpreter. Because
some locals have very different lifetimes, we will have two implementation
strategies. For locals that aren't used in closures, we'll keep them just as
they are on the stack. When a local is captured by a closure, we'll adopt
another solution that lifts them onto the heap where they can live as long as
needed.
-->
这意味着要比 Java 解释器里用的办法更复杂。因为有些局部变量的寿命截然不同，我们会采用两套实现策略。不被闭包使用的局部变量，仍原样留在栈上。一旦某个局部变量被闭包捕获，我们就换另一套方案，把它抬到堆上，好让它想活多久就活多久。

<!--
Closures have been around since the early Lisp days when bytes of memory and CPU
cycles were more precious than emeralds. Over the intervening decades, hackers
devised all <span name="lambda">manner</span> of ways to compile closures to
optimized runtime representations. Some are more efficient but require a more
complex compilation process than we could easily retrofit into clox.
-->
闭包自早期 Lisp 时代就有了——那时内存字节和 CPU 周期比翡翠还珍贵。这中间几十年里，黑客们发明了各<span name="lambda">式各样</span>的办法，把闭包编译成优化过的运行时表示。有些更高效，但需要的编译过程比我们能轻易塞进 clox 的要复杂得多。

<aside name="lambda">

<!--
Search for "closure conversion" or "lambda lifting" to start exploring.
-->
搜一下 “closure conversion” 或 “lambda lifting”，就能开始探索。

</aside>

<!--
The technique I explain here comes from the design of the Lua VM. It is fast,
parsimonious with memory, and implemented with relatively little code. Even more
impressive, it fits naturally into the single-pass compilers clox and Lua both
use. It is somewhat intricate, though. It might take a while before all the
pieces click together in your mind. We'll build them one step at a time, and
I'll try to introduce the concepts in stages.
-->
我这里讲解的技巧，来自 Lua 虚拟机的设计。它快、省内存，而且用相对不多的代码就能实现。更令人印象深刻的是，它自然地契合 clox 与 Lua 都采用的单遍编译器。不过它也有些曲折——所有碎片在你脑子里咔哒一声拼齐，可能得花点时间。我们一步一步搭，我会尽量分阶段引入概念。

<!--
-- Closure Objects
-->
## 闭包对象

<!--
Our VM represents functions at runtime using ObjFunction. These objects are
created by the front end during compilation. At runtime, all the VM does is load
the function object from a constant table and bind it to a name. There is no
operation to "create" a function at runtime. Much like string and number <span
name="literal">literals</span>, they are constants instantiated purely at
compile time.
-->
我们的虚拟机在运行时用 ObjFunction 表示函数。这些对象由前端在编译期创建。运行时，虚拟机所做的只是从常量表里加载函数对象，并把它绑定到一个名字。并没有什么在运行时“创建”函数的操作。很像字符串和数字<span name="literal">字面量</span>，它们是纯在编译期实例化的常量。

<aside name="literal">

<!--
In other words, a function declaration in Lox *is* a kind of literal -- a piece
of syntax that defines a constant value of a built-in type.
-->
换句话说，Lox 里的函数声明*就是*一种字面量——一段定义内置类型常量值的语法。

</aside>

<!--
That made sense because all of the data that composes a function is known at
compile time: the chunk of bytecode compiled from the function's body, and the
constants used in the body. Once we introduce closures, though, that
representation is no longer sufficient. Take a gander at:
-->
这说得通，因为构成函数的全部数据在编译期就已知：从函数体编译出的那块字节码，以及函数体里用到的常量。可一旦引入闭包，这种表示就不够用了。瞧瞧这个：

```lox
fun makeClosure(value) {
  fun closure() {
    print value;
  }
  return closure;
}

var doughnut = makeClosure("doughnut");
var bagel = makeClosure("bagel");
doughnut();
bagel();
```

<!--
The `makeClosure()` function defines and returns a function. We call it twice
and get two closures back. They are created by the same nested function
declaration `closure`, but close over different values. When we call the two
closures, each prints a different string. That implies we need some runtime
representation for a closure that captures the local variables surrounding the
function as they exist when the function declaration is *executed*, not just
when it is compiled.
-->
`makeClosure()` 定义并返回一个函数。我们调用它两次，得到两个闭包。它们由同一条嵌套函数声明 `closure` 创建，却关闭了不同的值。调用这两个闭包时，各自打印不同的字符串。这意味着我们需要某种运行时表示：闭包要捕获的是函数声明被*执行*时外围局部变量的模样，而不只是编译时的样子。

<!--
We'll work our way up to capturing variables, but a good first step is defining
that object representation. Our existing ObjFunction type represents the <span
name="raw">"raw"</span> compile-time state of a function declaration, since all
closures created from a single declaration share the same code and constants. At
runtime, when we execute a function declaration, we wrap the ObjFunction in a
new ObjClosure structure. The latter has a reference to the underlying bare
function along with runtime state for the variables the function closes over.
-->
我们会一步步走到捕获变量，但好的第一步是定义那种对象表示。现有的 ObjFunction 类型表示函数声明的<span name="raw">“生”</span>编译期状态——因为同一条声明创建的所有闭包共享同一份代码和常量。运行时，执行函数声明时，我们把 ObjFunction 包进一个新的 ObjClosure 结构。后者持有对底层裸函数的引用，以及函数所关闭的那些变量的运行时状态。

<aside name="raw">

<!--
The Lua implementation refers to the raw function object containing the bytecode
as a "prototype", which is a great word to describe this, except that word also
gets overloaded to refer to [prototypal inheritance][].

[prototypal inheritance]: https://en.wikipedia.org/wiki/Prototype-based_programming
-->
Lua 的实现把装字节码的那个生函数对象叫做 “prototype”（原型）——用来描述这东西很贴切，只可惜这词也被拿去指[原型继承][prototypal inheritance]了。

[prototypal inheritance]: https://en.wikipedia.org/wiki/Prototype-based_programming

</aside>

<img src="image/closures/obj-closure.png" alt="An ObjClosure with a reference to an ObjFunction."/>

<!--
We'll wrap every function in an ObjClosure, even if the function doesn't
actually close over and capture any surrounding local variables. This is a
little wasteful, but it simplifies the VM because we can always assume that the
function we're calling is an ObjClosure. That new struct starts out like this:
-->
我们会把每个函数都包进 ObjClosure，即便它其实并不关闭、也不捕获任何外围局部变量。这有点浪费，却能简化虚拟机——我们可以始终假定正在调用的函数是 ObjClosure。那个新结构体起步长这样：

^code obj-closure

<!--
Right now, it simply points to an ObjFunction and adds the necessary object
header stuff. Grinding through the usual ceremony for adding a new object type
to clox, we declare a C function to create a new closure.
-->
眼下它只是指向一个 ObjFunction，并加上必要的对象头那一套。走完给 clox 加新对象类型的惯常仪式，我们声明一个用来创建新闭包的 C 函数。

^code new-closure-h (2 before, 1 after)

<!--
Then we implement it here:
-->
然后在这边实现它：

^code new-closure

<!--
It takes a pointer to the ObjFunction it wraps. It also initializes the type
field to a new type.
-->
它接受指向所包装的 ObjFunction 的指针，并把类型字段初始化成一个新类型。

^code obj-type-closure (1 before, 1 after)

<!--
And when we're done with a closure, we release its memory.
-->
用完一个闭包后，释放它的内存。

^code free-closure (1 before, 1 after)

<!--
We free only the ObjClosure itself, not the ObjFunction. That's because the
closure doesn't *own* the function. There may be multiple closures that all
reference the same function, and none of them claims any special privilege over
it. We can't free the ObjFunction until *all* objects referencing it are gone --
including even the surrounding function whose constant table contains it.
Tracking that sounds tricky, and it is! That's why we'll write a garbage
collector soon to manage it for us.
-->
我们只释放 ObjClosure 本身，不释放 ObjFunction。因为闭包并不*拥有*那个函数。可能有多个闭包都引用同一个函数，谁也不比谁更有特权。在*所有*引用它的对象都消失之前——甚至包括常量表里装着它的那个外围函数——我们都不能释放 ObjFunction。追踪这些听起来就棘手，而且确实棘手！所以我们很快会写一个垃圾收集器来替我们管。

<!--
We also have the usual <span name="macro">macros</span> for checking a value's
type.
-->
我们也有检查值类型的惯常<span name="macro">宏</span>。

<aside name="macro">

<!--
Perhaps I should have defined a macro to make it easier to generate these
macros. Maybe that would be a little too meta.
-->
或许我该再定义一个宏，好让生成这些宏更轻松。不过那样也许有点太 meta 了。

</aside>

^code is-closure (2 before, 1 after)

<!--
And to cast a value:
-->
以及把值转型：

^code as-closure (2 before, 1 after)

<!--
Closures are first-class objects, so you can print them.
-->
闭包是一等对象，所以你可以打印它们。

^code print-closure (1 before, 1 after)

<!--
They display exactly as ObjFunction does. From the user's perspective, the
difference between ObjFunction and ObjClosure is purely a hidden implementation
detail. With that out of the way, we have a working but empty representation for
closures.
-->
它们显示出来和 ObjFunction 一模一样。从用户角度看，ObjFunction 与 ObjClosure 的差别纯粹是隐藏的实现细节。搞定这些之后，我们便有了一个能用、却还空荡荡的闭包表示。

<!--
-- Compiling to closure objects
-->
### 编译为闭包对象

<!--
We have closure objects, but our VM never creates them. The next step is getting
the compiler to emit instructions to tell the runtime when to create a new
ObjClosure to wrap a given ObjFunction. This happens right at the end of a
function declaration.
-->
我们有了闭包对象，可虚拟机从不创建它们。下一步是让编译器发出指令，告诉运行时何时该创建一个新的 ObjClosure 来包装给定的 ObjFunction。这发生在函数声明的正末尾。

^code emit-closure (1 before, 1 after)

<!--
Before, the final bytecode for a function declaration was a single `OP_CONSTANT`
instruction to load the compiled function from the surrounding function's
constant table and push it onto the stack. Now we have a new instruction.
-->
以前，函数声明最终的字节码是一条单独的 `OP_CONSTANT` 指令，从外围函数的常量表里加载已编译的函数，并压入栈。现在我们有了一条新指令。

^code closure-op (1 before, 1 after)

<!--
Like `OP_CONSTANT`, it takes a single operand that represents a constant table
index for the function. But when we get over to the runtime implementation, we
do something more interesting.
-->
和 `OP_CONSTANT` 一样，它接受一个表示函数在常量表中下标的操作数。但到了运行时的实现，我们会做更有意思的事。

<!--
First, let's be diligent VM hackers and slot in disassembler support for the
instruction.
-->
首先，做个勤勉的虚拟机黑客，给这条指令装上反汇编支持。

^code disassemble-closure (2 before, 1 after)

<!--
There's more going on here than we usually have in the disassembler. By the end
of the chapter, you'll discover that `OP_CLOSURE` is quite an unusual
instruction. It's straightforward right now -- just a single byte operand -- but
we'll be adding to it. This code here anticipates that future.
-->
这儿发生的事，比我们在反汇编器里通常见到的多。到本章末尾你会发现，`OP_CLOSURE` 是一条相当不寻常的指令。眼下它还直截了当——只有一个单字节操作数——但我们还会往上面加东西。这里的代码是在为那未来铺垫。

<!--
-- Interpreting function declarations
-->
### 解释函数声明

<!--
Most of the work we need to do is in the runtime. We have to handle the new
instruction, naturally. But we also need to touch every piece of code in the VM
that works with ObjFunction and change it to use ObjClosure instead -- function
calls, call frames, etc. We'll start with the instruction, though.
-->
我们要做的大部分工作在运行时。当然得处理新指令。但我们还得触碰虚拟机里所有和 ObjFunction 打交道的代码，改成用 ObjClosure——函数调用、调用帧，等等。不过先从指令开始。

^code interpret-closure (1 before, 1 after)

<!--
Like the `OP_CONSTANT` instruction we used before, first we load the compiled
function from the constant table. The difference now is that we wrap that
function in a new ObjClosure and push the result onto the stack.
-->
和以前用的 `OP_CONSTANT` 一样，先从常量表加载已编译的函数。不同之处在于，我们现在把那个函数包进一个新的 ObjClosure，再把结果压栈。

<!--
Once you have a closure, you'll eventually want to call it.
-->
有了闭包，你终究会想调用它。

^code call-value-closure (1 before, 1 after)

<!--
We remove the code for calling objects whose type is `OBJ_FUNCTION`. Since we
wrap all functions in ObjClosures, the runtime will never try to invoke a bare
ObjFunction anymore. Those objects live only in constant tables and get
immediately <span name="naked">wrapped</span> in closures before anything else
sees them.
-->
我们删掉调用类型为 `OBJ_FUNCTION` 的对象的那段代码。既然所有函数都包在 ObjClosure 里，运行时再也不会试图调用一个裸的 ObjFunction。那些对象只住在常量表里，并在任何别的东西看见它们之前，立刻被<span name="naked">包</span>进闭包。

<aside name="naked">

<!--
We don't want any naked functions wandering around the VM! What would the
neighbors say?
-->
我们可不想让任何裸函数在虚拟机里晃荡！邻居们会怎么说？

</aside>

<!--
We replace the old code with very similar code for calling a closure instead.
The only difference is the type of object we pass to `call()`. The real changes
are over in that function. First, we update its signature.
-->
我们用非常相似的、改为调用闭包的代码替换旧代码。唯一差别是传给 `call()` 的对象类型。真正的改动在那个函数里。首先，更新它的签名。

^code call-signature (1 after)

<!--
Then, in the body, we need to fix everything that referenced the function to
handle the fact that we've introduced a layer of indirection. We start with the
arity checking:
-->
然后，在函数体里，凡是引用了函数的地方都要修好，以应付我们引入的那一层间接。先从 arity 检查开始：

^code check-arity (1 before, 1 after)

<!--
The only change is that we unwrap the closure to get to the underlying function.
The next thing `call()` does is create a new CallFrame. We change that code to
store the closure in the CallFrame and get the bytecode pointer from the
closure's function.
-->
唯一的变化是解开闭包以到达底层函数。接下来 `call()` 要做的是创建新的 CallFrame。我们改那段代码，把闭包存进 CallFrame，并从闭包的函数里取得字节码指针。

^code call-init-closure (1 before, 1 after)

<!--
This necessitates changing the declaration of CallFrame too.
-->
这也迫使我们改动 CallFrame 的声明。

^code call-frame-closure (1 before, 1 after)

<!--
That change triggers a few other cascading changes. Every place in the VM that
accessed CallFrame's function needs to use a closure instead. First, the macro
for reading a constant from the current function's constant table:
-->
那一改又牵出几处连锁变化。虚拟机里凡访问 CallFrame 的 function 的地方，都要改用闭包。首先是从当前函数常量表读常量的宏：

^code read-constant (2 before, 2 after)

<!--
When `DEBUG_TRACE_EXECUTION` is enabled, it needs to get to the chunk from the
closure.
-->
启用 `DEBUG_TRACE_EXECUTION` 时，它需要从闭包拿到 chunk。

^code disassemble-instruction (1 before, 1 after)

<!--
Likewise when reporting a runtime error:
-->
报告运行时错误时同理：

^code runtime-error-function (1 before, 1 after)

<!--
Almost there. The last piece is the blob of code that sets up the very first
CallFrame to begin executing the top-level code for a Lox script.
-->
快到了。最后一块是设置最初那个 CallFrame、开始执行 Lox 脚本顶层代码的那坨代码。

^code interpret (1 before, 2 after)

<!--
<span name="pop">The</span> compiler still returns a raw ObjFunction when
compiling a script. That's fine, but it means we need to wrap it in an
ObjClosure here, before the VM can execute it.
-->
<span name="pop">编译器</span>编译脚本时仍返回一个生的 ObjFunction。这没关系，但意味着在虚拟机能执行它之前，我们得在这里把它包进 ObjClosure。

<aside name="pop">

<!--
The code looks a little silly because we still push the original ObjFunction
onto the stack. Then we pop it after creating the closure, only to then push the
closure. Why put the ObjFunction on there at all? As usual, when you see weird
stack stuff going on, it's to keep the [forthcoming garbage collector][gc] aware
of some heap-allocated objects.

[gc]: garbage-collection.html
-->
这段代码看起来有点傻：我们仍把原来的 ObjFunction 压栈，创建闭包后再弹出它，然后又把闭包压上去。何必把 ObjFunction 放上去呢？照例，你看到奇怪的栈操作时，多半是为了让[即将到来的垃圾收集器][gc]知道某些堆上分配的对象。

[gc]: garbage-collection.html

</aside>

<!--
We are back to a working interpreter. The *user* can't tell any difference, but
the compiler now generates code telling the VM to create a closure for each
function declaration. Every time the VM executes a function declaration, it
wraps the ObjFunction in a new ObjClosure. The rest of the VM now handles those
ObjClosures floating around. That's the boring stuff out of the way. Now we're
ready to make these closures actually *do* something.
-->
我们又回到了一个能工作的解释器。*用户*看不出任何差别，但编译器现在会生成代码，告诉虚拟机为每个函数声明创建一个闭包。虚拟机每执行一次函数声明，就把 ObjFunction 包进一个新的 ObjClosure。虚拟机其余部分现在处理这些漂浮的 ObjClosure。无聊的部分清掉了。现在，我们准备好让这些闭包真正*干点事*。

<!--
-- Upvalues
-->
## 上值（upvalue）

<!--
Our existing instructions for reading and writing local variables are limited to
a single function's stack window. Locals from a surrounding function are outside
of the inner function's window. We're going to need some new instructions.
-->
我们现有读写局部变量的指令，局限于单个函数的栈窗口。外围函数的局部变量落在内层函数窗口之外。我们需要一些新指令。

<!--
The easiest approach might be an instruction that takes a relative stack slot
offset that can reach *before* the current function's window. That would work if
closed-over variables were always on the stack. But as we saw earlier, these
variables sometimes outlive the function where they are declared. That means
they won't always be on the stack.
-->
最简单的办法或许是一条指令，接受一个相对栈槽偏移，能伸到当前函数窗口*之前*。若被关闭的变量始终在栈上，这行得通。但如前所述，这些变量有时比声明它们的函数活得更久——这意味着它们并不总在栈上。

<!--
The next easiest approach, then, would be to take any local variable that gets
closed over and have it always live on the heap. When the local variable
declaration in the surrounding function is executed, the VM would allocate
memory for it dynamically. That way it could live as long as needed.
-->
那么次简单的办法，是让任何被关闭的局部变量始终住在堆上。外围函数里执行该局部变量声明时，虚拟机动态为它分配内存。这样它想活多久就活多久。

<!--
This would be a fine approach if clox didn't have a single-pass compiler. But
that restriction we chose in our implementation makes things harder. Take a look
at this example:
-->
若 clox 没有单遍编译器，这会是个不错的方案。但我们在实现里选的那条限制，把事情弄难了。看看这个例子：

```lox
fun outer() {
  var x = 1;    // (1)
  x = 2;        // (2)
  fun inner() { // (3)
    print x;
  }
  inner();
}
```

<!--
Here, the compiler compiles the declaration of `x` at `(1)` and emits code for
the assignment at `(2)`. It does that before reaching the declaration of
`inner()` at `(3)` and discovering that `x` is in fact closed over. We don't
have an easy way to go back and fix that already-emitted code to treat `x`
specially. Instead, we want a solution that allows a closed-over variable to
live on the stack exactly like a normal local variable *until the point that it
is closed over*.
-->
这里，编译器在 `(1)` 编译 `x` 的声明，并在 `(2)` 为赋值发出代码。它在到达 `(3)` 处 `inner()` 的声明、发现 `x` 其实被关闭之前，就已经做完这些了。我们没法轻易回头去改已经发出的代码，让它特殊对待 `x`。相反，我们想要一种方案：被关闭的变量可以像普通局部变量一样住在栈上，*直到它被关闭的那一刻*。

<!--
Fortunately, thanks to the Lua dev team, we have a solution. We use a level of
indirection that they call an **upvalue**. An upvalue refers to a local variable
in an enclosing function. Every closure maintains an array of upvalues, one for
each surrounding local variable that the closure uses.
-->
幸好，多亏 Lua 开发团队，我们有了办法。我们使用他们称为 **上值（upvalue）** 的一层间接。上值指向外围函数中的一个局部变量。每个闭包维护一个上值数组，闭包用到的每一个外围局部变量各占一项。

<!--
The upvalue points back into the stack to where the variable it captured lives.
When the closure needs to access a closed-over variable, it goes through the
corresponding upvalue to reach it. When a function declaration is first executed
and we create a closure for it, the VM creates the array of upvalues and wires
them up to "capture" the surrounding local variables that the closure needs.
-->
上值指回栈上、它所捕获的变量所在之处。闭包需要访问被关闭的变量时，经由对应的上值到达它。函数声明首次执行、我们为它创建闭包时，虚拟机创建上值数组，并把它们接线好，以“捕获”闭包所需的那些外围局部变量。

<!--
For example, if we throw this program at clox,
-->
比方说，若把这个程序扔给 clox，

```lox
{
  var a = 3;
  fun f() {
    print a;
  }
}
```

<!--
the compiler and runtime will conspire together to build up a set of objects in
memory like this:
-->
编译器与运行时会联手在内存里搭出这样一组对象：

<img src="image/closures/open-upvalue.png" alt="The object graph of the stack, ObjClosure, ObjFunction, and upvalue array."/>

<!--
That might look overwhelming, but fear not. We'll work our way through it. The
important part is that upvalues serve as the layer of indirection needed to
continue to find a captured local variable even after it moves off the stack.
But before we get to all that, let's focus on compiling captured variables.
-->
这看上去或许铺天盖地，但别怕——我们会一路拆开。要紧的是：上值充当所需的那层间接，好让被捕获的局部变量即便离开栈，仍能被找到。不过在进入那一切之前，先专注于编译被捕获的变量。

<!--
-- Compiling upvalues
-->
### 编译上值

<!--
As usual, we want to do as much work as possible during compilation to keep
execution simple and fast. Since local variables are lexically scoped in Lox, we
have enough knowledge at compile time to resolve which surrounding local
variables a function accesses and where those locals are declared. That, in
turn, means we know *how many* upvalues a closure needs, *which* variables they
capture, and *which stack slots* contain those variables in the declaring
function's stack window.
-->
照例，我们想在编译期尽量多干活，好让执行保持简单而快速。既然 Lox 里局部变量是词法作用域的，编译期就有足够知识，能解析出函数访问了哪些外围局部变量、它们声明在何处。这进而意味着我们知道闭包需要*多少*上值、它们捕获*哪些*变量，以及在声明函数的栈窗口里，*哪些栈槽*装着那些变量。

<!--
Currently, when the compiler resolves an identifier, it walks the block scopes
for the current function from innermost to outermost. If we don't find the
variable in that function, we assume the variable must be a global. We don't
consider the local scopes of enclosing functions -- they get skipped right over.
The first change, then, is inserting a resolution step for those outer local
scopes.
-->
目前，编译器解析标识符时，从最内到最外走当前函数的块作用域。若在该函数里找不到变量，就假定它一定是全局的。我们不考虑外围函数的局部作用域——它们直接被跳过。那么第一处改动，就是为那些外层局部作用域插入一步解析。

^code named-variable-upvalue (3 before, 1 after)

<!--
This new `resolveUpvalue()` function looks for a local variable declared in any
of the surrounding functions. If it finds one, it returns an "upvalue index" for
that variable. (We'll get into what that means later.) Otherwise, it returns -1
to indicate the variable wasn't found. If it was found, we use these two new
instructions for reading or writing to the variable through its upvalue:
-->
这个新的 `resolveUpvalue()` 函数在任意外围函数里查找声明的局部变量。若找到，就返回该变量的“上值下标”。（后文再讲那是什么意思。）否则返回 -1，表示没找到。若找到了，我们用这两条新指令，经由其上值读写该变量：

^code upvalue-ops (1 before, 1 after)

<!--
We're implementing this sort of top-down, so I'll show you how these work at
runtime soon. The part to focus on now is how the compiler actually resolves the
identifier.
-->
我们大致是自上而下实现的，所以很快会展示它们在运行时如何工作。眼下要聚焦的，是编译器究竟如何解析标识符。

^code resolve-upvalue

<!--
We call this after failing to resolve a local variable in the current function's
scope, so we know the variable isn't in the current compiler. Recall that
Compiler stores a pointer to the Compiler for the enclosing function, and these
pointers form a linked chain that goes all the way to the root Compiler for the
top-level code. Thus, if the enclosing Compiler is `NULL`, we know we've reached
the outermost function without finding a local variable. The variable must be
<span name="undefined">global</span>, so we return -1.
-->
我们在当前函数作用域里解析局部变量失败之后调用它，因此知道变量不在当前编译器里。回想一下：Compiler 存着指向外围函数 Compiler 的指针，这些指针连成一条链，一直通到顶层代码的根 Compiler。因此，若外围 Compiler 是 `NULL`，我们就知道已到达最外层函数仍未找到局部变量。这变量必定是<span name="undefined">全局</span>的，于是返回 -1。

<aside name="undefined">

<!--
It might end up being an entirely undefined variable and not even global. But in
Lox, we don't detect that error until runtime, so from the compiler's
perspective, it's "hopefully global".
-->
它最终也可能是个完全未定义的变量，甚至不是全局的。但在 Lox 里，我们到运行时才检测那个错误，所以从编译器的角度看，它是“但愿是全局吧”。

</aside>

<!--
Otherwise, we try to resolve the identifier as a *local* variable in the
*enclosing* compiler. In other words, we look for it right outside the current
function. For example:
-->
否则，我们试着在*外围*编译器里把它解析为*局部*变量。换句话说，就在当前函数外侧找它。例如：

```lox
fun outer() {
  var x = 1;
  fun inner() {
    print x; // (1)
  }
  inner();
}
```

<!--
When compiling the identifier expression at `(1)`, `resolveUpvalue()` looks for
a local variable `x` declared in `outer()`. If found -- like it is in this
example -- then we've successfully resolved the variable. We create an upvalue
so that the inner function can access the variable through that. The upvalue is
created here:
-->
编译 `(1)` 处的标识符表达式时，`resolveUpvalue()` 在 `outer()` 里查找声明的局部变量 `x`。若找到——像本例这样——我们就成功解析了变量。我们创建一个上值，好让内层函数能经由它访问该变量。上值在这里创建：

^code add-upvalue

<!--
The compiler keeps an array of upvalue structures to track the closed-over
identifiers that it has resolved in the body of each function. Remember how the
compiler's Local array mirrors the stack slot indexes where locals live at
runtime? This new upvalue array works the same way. The indexes in the
compiler's array match the indexes where upvalues will live in the ObjClosure at
runtime.
-->
编译器为每个函数体维护一个上值结构数组，追踪它已解析到的那些被关闭的标识符。还记得编译器的 Local 数组如何镜像局部变量在运行时栈槽下标吗？这个新的上值数组也是同一套路。编译器数组里的下标，与运行时上值在 ObjClosure 里的下标一致。

<!--
This function adds a new upvalue to that array. It also keeps track of the
number of upvalues the function uses. It stores that count directly in the
ObjFunction itself because we'll also <span name="bridge">need</span> that
number for use at runtime.
-->
这个函数往那个数组里加一个新上值。它还跟踪函数使用的上值个数。它把那计数直接存在 ObjFunction 本身里，因为运行时我们也<span name="bridge">需要</span>这个数字。

<aside name="bridge">

<!--
Like constants and function arity, the upvalue count is another one of those
little pieces of data that form the bridge between the compiler and runtime.
-->
和常量、函数 arity 一样，上值计数是那些在编译器与运行时之间架桥的小片数据之一。

</aside>

<!--
The `index` field tracks the closed-over local variable's slot index. That way
the compiler knows *which* variable in the enclosing function needs to be
captured. We'll circle back to what that `isLocal` field is for before too long.
Finally, `addUpvalue()` returns the index of the created upvalue in the
function's upvalue list. That index becomes the operand to the `OP_GET_UPVALUE`
and `OP_SET_UPVALUE` instructions.
-->
`index` 字段追踪被关闭局部变量的槽下标。这样编译器知道外围函数里*哪一个*变量需要被捕获。那个 `isLocal` 字段是干什么的，我们很快会绕回来。最后，`addUpvalue()` 返回所创建上值在函数上值列表中的下标。那下标成为 `OP_GET_UPVALUE` 与 `OP_SET_UPVALUE` 指令的操作数。

<!--
That's the basic idea for resolving upvalues, but the function isn't fully
baked. A closure may reference the same variable in a surrounding function
multiple times. In that case, we don't want to waste time and memory creating a
separate upvalue for each identifier expression. To fix that, before we add a
new upvalue, we first check to see if the function already has an upvalue that
closes over that variable.
-->
这就是解析上值的基本想法，但函数还没完全烤熟。闭包可能多次引用外围函数里的同一个变量。那种情况下，我们不想浪费时间和内存，为每个标识符表达式各造一个上值。要修好这点，在添加新上值之前，先检查函数是否已有关闭该变量的上值。

^code existing-upvalue (1 before, 1 after)

<!--
If we find an upvalue in the array whose slot index matches the one we're
adding, we just return that *upvalue* index and reuse it. Otherwise, we fall
through and add the new upvalue.
-->
若在数组里找到槽下标与我们要添加的相匹配的上值，就直接返回那个*上值*下标并复用它。否则继续往下，添加新上值。

<!--
These two functions access and modify a bunch of new state, so let's define
that. First, we add the upvalue count to ObjFunction.
-->
这两个函数访问并修改一堆新状态，所以来定义它们。首先，把上值计数加到 ObjFunction。

^code upvalue-count (1 before, 1 after)

<!--
We're conscientious C programmers, so we zero-initialize that when an
ObjFunction is first allocated.
-->
我们是尽职的 C 程序员，所以 ObjFunction 首次分配时把它零初始化。

^code init-upvalue-count (1 before, 1 after)

<!--
In the compiler, we add a field for the upvalue array.
-->
在编译器里，我们为上值数组加一个字段。

^code upvalues-array (1 before, 1 after)

<!--
For simplicity, I gave it a fixed size. The `OP_GET_UPVALUE` and
`OP_SET_UPVALUE` instructions encode an upvalue index using a single byte
operand, so there's a restriction on how many upvalues a function can have --
how many unique variables it can close over. Given that, we can afford a static
array that large. We also need to make sure the compiler doesn't overflow that
limit.
-->
为简单起见，我给了它固定大小。`OP_GET_UPVALUE` 和 `OP_SET_UPVALUE` 用单字节操作数编码上值下标，因此函数能有多少上值——能关闭多少个不同变量——是有上限的。有了那上限，我们负担得起那么大的静态数组。还得确保编译器不会溢出那个限制。

^code too-many-upvalues (5 before, 1 after)

<!--
Finally, the Upvalue struct type itself.
-->
最后，是 Upvalue 结构体类型本身。

^code upvalue-struct

<!--
The `index` field stores which local slot the upvalue is capturing. The
`isLocal` field deserves its own section, which we'll get to next.
-->
`index` 字段存放上值正在捕获哪个局部槽。`isLocal` 字段值得单独一节，下一节就讲。

<!--
-- Flattening upvalues
-->
### 展平上值

<!--
In the example I showed before, the closure is accessing a variable declared in
the immediately enclosing function. Lox also supports accessing local variables
declared in *any* enclosing scope, as in:
-->
在我先前展示的例子里，闭包访问的是紧邻外围函数里声明的变量。Lox 也支持访问声明在*任意*外围作用域里的局部变量，比如：

```lox
fun outer() {
  var x = 1;
  fun middle() {
    fun inner() {
      print x;
    }
  }
}
```

<!--
Here, we're accessing `x` in `inner()`. That variable is defined not in
`middle()`, but all the way out in `outer()`. We need to handle cases like this
too. You *might* think that this isn't much harder since the variable will
simply be somewhere farther down on the stack. But consider this <span
name="devious">devious</span> example:
-->
这里，我们在 `inner()` 里访问 `x`。那变量并不定义在 `middle()` 里，而是远在 `outer()` 中。这类情况也得处理。你*或许*会想这难不了多少，因为变量不过是在栈上更靠下的某处。但看看这个<span name="devious">阴险</span>的例子：

<aside name="devious">

<!--
If you work on programming languages long enough, you will develop a
finely honed skill at creating bizarre programs like this that are technically
valid but likely to trip up an implementation written by someone with a less
perverse imagination than you.
-->
若你在编程语言上干得够久，就会练出一手精细本事：造出这种技术上合法、却很可能绊倒想象力没你那么邪门的人写出的实现的古怪程序。

</aside>

```lox
fun outer() {
  var x = "value";
  fun middle() {
    fun inner() {
      print x;
    }

    print "create inner closure";
    return inner;
  }

  print "return from outer";
  return middle;
}

var mid = outer();
var in = mid();
in();
```

<!--
When you run this, it should print:
-->
跑起来时，它应当打印：

```text
return from outer
create inner closure
value
```

<!--
I know, it's convoluted. The important part is that `outer()` -- where `x` is
declared -- returns and pops all of its variables off the stack before the
*declaration* of `inner()` executes. So, at the point in time that we create the
closure for `inner()`, `x` is already off the stack.
-->
我知道，这绕得很。要紧的是：声明 `x` 的 `outer()` 在 `inner()` 的*声明*执行之前就已经返回，并把所有变量从栈上弹出了。因此，我们为 `inner()` 创建闭包的那一刻，`x` 已经不在栈上了。

<!--
Here, I traced out the execution flow for you:
-->
这儿，我替你把执行流程描出来了：

<img src="image/closures/execution-flow.png" alt="Tracing through the previous example program."/>

<!--
See how `x` is popped &#9312; before it is captured &#9313; and then later
accessed &#9314;? We really have two problems:
-->
看到了吗？`x` 先被弹出 &#9312;，然后才被捕获 &#9313;，再后来才被访问 &#9314;？我们其实有两个问题：

<!--
1.  We need to resolve local variables that are declared in surrounding
    functions beyond the immediately enclosing one.

2.  We need to be able to capture variables that have already left the stack.
-->
1.  我们需要解析声明在紧邻外围之外、更远外围函数里的局部变量。

2.  我们需要能捕获已经离开栈的变量。

<!--
Fortunately, we're in the middle of adding upvalues to the VM, and upvalues are
explicitly designed for tracking variables that have escaped the stack. So, in a
clever bit of self-reference, we can use upvalues to allow upvalues to capture
variables declared outside of the immediately surrounding function.
-->
幸好，我们正给虚拟机加上值，而上值正是为追踪已逃出栈的变量而设计的。于是，在一点点巧妙的自我指涉里，我们可以用上值让上值去捕获声明在紧邻外围函数之外的变量。

<!--
The solution is to allow a closure to capture either a local variable or *an
existing upvalue* in the immediately enclosing function. If a deeply nested
function references a local variable declared several hops away, we'll thread it
through all of the intermediate functions by having each function capture an
upvalue for the next function to grab.
-->
办法是：允许闭包捕获紧邻外围函数里的局部变量，*或者已有的上值*。若深层嵌套的函数引用了隔好几跳才声明的局部变量，我们就让每个中间函数各捕获一个上值，供下一层函数去抓，从而把变量串过所有中间函数。

<img src="image/closures/linked-upvalues.png" alt="An upvalue in inner() points to an upvalue in middle(), which points to a local variable in outer()."/>

<!--
In the above example, `middle()` captures the local variable `x` in the
immediately enclosing function `outer()` and stores it in its own upvalue. It
does this even though `middle()` itself doesn't reference `x`. Then, when the
declaration of `inner()` executes, its closure grabs the *upvalue* from the
ObjClosure for `middle()` that captured `x`. A function captures -- either a
local or upvalue -- *only* from the immediately surrounding function, which is
guaranteed to still be around at the point that the inner function declaration
executes.
-->
在上面的例子里，`middle()` 捕获紧邻外围函数 `outer()` 里的局部变量 `x`，并存进自己的上值。即便 `middle()` 本身并不引用 `x`，它也这么做。然后，当 `inner()` 的声明执行时，其闭包从 `middle()` 的 ObjClosure 里抓取那个捕获了 `x` 的*上值*。函数——无论捕获局部还是上值——*只*从紧邻外围函数捕获，而后者在内层函数声明执行时保证仍在。

<!--
In order to implement this, `resolveUpvalue()` becomes recursive.
-->
要实现这一点，`resolveUpvalue()` 变成递归的。

^code resolve-upvalue-recurse (4 before, 1 after)

<!--
It's only another three lines of code, but I found this function really
challenging to get right the first time. This in spite of the fact that I wasn't
inventing anything new, just porting the concept over from Lua. Most recursive
functions either do all their work before the recursive call (a **pre-order
traversal**, or "on the way down"), or they do all the work after the recursive
call (a **post-order traversal**, or "on the way back up"). This function does
both. The recursive call is right in the middle.
-->
不过又是三行代码，可我第一次要把这函数写对时，却觉得真难。尽管我并没发明新东西，只是把概念从 Lua 移植过来。多数递归函数要么在递归调用前做完全部工作（**前序遍历**，或曰“下行途中”），要么在递归调用后做完全部工作（**后序遍历**，或曰“回程途中”）。这函数两头都干。递归调用正落在中间。

<!--
We'll walk through it slowly. First, we look for a matching local variable in
the enclosing function. If we find one, we capture that local and return. That's
the <span name="base">base</span> case.
-->
我们慢慢走一遍。首先，在外围函数里找匹配的局部变量。若找到，就捕获那个局部并返回。那是<span name="base">基本情况</span>。

<aside name="base">

<!--
The other base case, of course, is if there is no enclosing function. In that
case, the variable can't be resolved lexically and is treated as global.
-->
另一个基本情况，当然是没有外围函数。那种情况下，变量无法词法解析，就被当作全局。

</aside>

<!--
Otherwise, we look for a local variable beyond the immediately enclosing
function. We do that by recursively calling `resolveUpvalue()` on the
*enclosing* compiler, not the current one. This series of `resolveUpvalue()`
calls works its way along the chain of nested compilers until it hits one of
the base cases -- either it finds an actual local variable to capture or it
runs out of compilers.
-->
否则，我们在紧邻外围之外寻找局部变量。做法是对*外围*编译器——不是当前这个——递归调用 `resolveUpvalue()`。这一连串 `resolveUpvalue()` 调用沿着嵌套编译器链往外走，直到撞上某个基本情况——要么找到真正可捕获的局部变量，要么编译器用尽。

<!--
When a local variable is found, the most deeply <span name="outer">nested</span>
call to `resolveUpvalue()` captures it and returns the upvalue index. That
returns to the next call for the inner function declaration. That call captures
the *upvalue* from the surrounding function, and so on. As each nested call to
`resolveUpvalue()` returns, we drill back down into the innermost function
declaration where the identifier we are resolving appears. At each step along
the way, we add an upvalue to the intervening function and pass the resulting
upvalue index down to the next call.
-->
找到局部变量时，最深<span name="outer">嵌套</span>的那次 `resolveUpvalue()` 调用捕获它并返回上值下标。那返回到内层函数声明的下一次调用。那次调用再从外围函数捕获*上值*，如此类推。随着每次嵌套的 `resolveUpvalue()` 返回，我们往下钻回出现该标识符的最内层函数声明。沿途每一步，我们给中间函数加一个上值，并把得到的上值下标传给下一次调用。

<aside name="outer">

<!--
Each recursive call to `resolveUpvalue()` walks *out* one level of function
nesting. So an inner *recursive call* refers to an *outer* nested declaration.
The innermost recursive call to `resolveUpvalue()` that finds the local variable
will be for the *outermost* function, just inside the enclosing function where
that variable is actually declared.
-->
每次对 `resolveUpvalue()` 的递归调用向外走一层函数嵌套。因此，一次内层的*递归调用*对应的是外层的嵌套声明。找到局部变量的那次最内层递归调用，对应的是*最外层*函数——就在真正声明该变量的外围函数内侧。

</aside>

<!--
It might help to walk through the original example when resolving `x`:
-->
解析 `x` 时，走一遍原先的例子或许有帮助：

<img src="image/closures/recursion.png" alt="Tracing through a recursive call to resolveUpvalue()."/>

<!--
Note that the new call to `addUpvalue()` passes `false` for the `isLocal`
parameter. Now you see that that flag controls whether the closure captures a
local variable or an upvalue from the surrounding function.
-->
注意，对新的 `addUpvalue()` 调用，`isLocal` 参数传的是 `false`。现在你明白了：那标志控制闭包捕获的是局部变量，还是外围函数里的上值。

<!--
By the time the compiler reaches the end of a function declaration, every
variable reference has been resolved as either a local, an upvalue, or a global.
Each upvalue may in turn capture a local variable from the surrounding function,
or an upvalue in the case of transitive closures. We finally have enough data to
emit bytecode which creates a closure at runtime that captures all of the
correct variables.
-->
等编译器走到函数声明末尾时，每个变量引用都已解析为局部、上值或全局。每个上值进而可能捕获外围函数的局部变量，或在传递闭包的情形下捕获一个上值。我们终于有足够数据，发出在运行时创建闭包、并捕获全部正确变量的字节码。

^code capture-upvalues (1 before, 1 after)

<!--
The `OP_CLOSURE` instruction is unique in that it has a variably sized encoding.
For each upvalue the closure captures, there are two single-byte operands. Each
pair of operands specifies what that upvalue captures. If the first byte is one,
it captures a local variable in the enclosing function. If zero, it captures one
of the function's upvalues. The next byte is the local slot or upvalue index to
capture.
-->
`OP_CLOSURE` 指令的独特之处在于它有可变长度编码。闭包捕获的每个上值对应两个单字节操作数。每对操作数指明那个上值捕获什么。若第一个字节是一，它捕获外围函数里的局部变量；若是零，则捕获该函数的某个上值。下一个字节是要捕获的局部槽或上值下标。

<!--
This odd encoding means we need some bespoke support in the disassembly code
for `OP_CLOSURE`.
-->
这古怪的编码意味着，我们需要在 `OP_CLOSURE` 的反汇编代码里做些定制支持。

^code disassemble-upvalues (1 before, 1 after)

<!--
For example, take this script:
-->
比方说，看这个脚本：

```lox
fun outer() {
  var a = 1;
  var b = 2;
  fun middle() {
    var c = 3;
    var d = 4;
    fun inner() {
      print a + c + b + d;
    }
  }
}
```

<!--
If we disassemble the instruction that creates the closure for `inner()`, it
prints this:
-->
若反汇编创建 `inner()` 闭包的那条指令，它打印出：

```text
0004    9 OP_CLOSURE          2 <fn inner>
0006      |                     upvalue 0
0008      |                     local 1
0010      |                     upvalue 1
0012      |                     local 2
```

<!--
We have two other, simpler instructions to add disassembler support for.
-->
还有另外两条更简单的指令要加反汇编支持。

^code disassemble-upvalue-ops (2 before, 1 after)

<!--
These both have a single-byte operand, so there's nothing exciting going on. We
do need to add an include so the debug module can get to `AS_FUNCTION()`.
-->
这两条都有单字节操作数，没什么刺激的。我们倒是需要加一条 include，好让 debug 模块能用到 `AS_FUNCTION()`。

^code debug-include-object (1 before, 1 after)

<!--
With that, our compiler is where we want it. For each function declaration, it
outputs an `OP_CLOSURE` instruction followed by a series of operand byte pairs
for each upvalue it needs to capture at runtime. It's time to hop over to that
side of the VM and get things running.
-->
如此，编译器就到了我们想要的位置。对每个函数声明，它输出一条 `OP_CLOSURE` 指令，后跟一串操作数字节对，对应运行时需要捕获的每个上值。该跳到虚拟机那一侧，把事情跑起来了。

<!--
-- Upvalue Objects
-->
## 上值对象

<!--
Each `OP_CLOSURE` instruction is now followed by the series of bytes that
specify the upvalues the ObjClosure should own. Before we process those
operands, we need a runtime representation for upvalues.
-->
每条 `OP_CLOSURE` 指令现在后面跟着一串字节，指明 ObjClosure 应拥有的上值。在处理那些操作数之前，我们需要上值的运行时表示。

^code obj-upvalue

<!--
We know upvalues must manage closed-over variables that no longer live on the
stack, which implies some amount of dynamic allocation. The easiest way to do
that in our VM is by building on the object system we already have. That way,
when we implement a garbage collector in [the next chapter][gc], the GC can
manage memory for upvalues too.
-->
我们知道上值必须管理那些不再住在栈上的被关闭变量，这意味着需要一定的动态分配。在我们的虚拟机里，最容易的做法是建立在已有的对象系统之上。这样，等我们在[下一章][gc]实现垃圾收集器时，GC 也能管理上值的内存。

[gc]: garbage-collection.html

<!--
Thus, our runtime upvalue structure is an ObjUpvalue with the typical Obj header
field. Following that is a `location` field that points to the closed-over
variable. Note that this is a *pointer* to a Value, not a Value itself. It's a
reference to a *variable*, not a *value*. This is important because it means
that when we assign to the variable the upvalue captures, we're assigning to the
actual variable, not a copy. For example:
-->
因此，我们的运行时上值结构是带着典型 Obj 头字段的 ObjUpvalue。其后是 `location` 字段，指向被关闭的变量。注意这是指向 Value 的*指针*，不是 Value 本身。它是对*变量*的引用，不是对*值*的引用。这很重要，因为这意味着给上值捕获的变量赋值时，我们赋的是真正的那个变量，而不是一份拷贝。例如：

```lox
fun outer() {
  var x = "before";
  fun inner() {
    x = "assigned";
  }
  inner();
  print x;
}
outer();
```

<!--
This program should print "assigned" even though the closure assigns to `x` and
the surrounding function accesses it.
-->
这个程序应打印 `"assigned"`，尽管是闭包给 `x` 赋值、外围函数去访问它。

<!--
Because upvalues are objects, we've got all the usual object machinery, starting
with a constructor-like function:
-->
因为上值是对象，我们有全套惯常的对象机制，从类似构造函数的函数开始：

^code new-upvalue-h (1 before, 1 after)

<!--
It takes the address of the slot where the closed-over variable lives. Here is
the implementation:
-->
它接受被关闭变量所在槽的地址。实现如下：

^code new-upvalue

<!--
We simply initialize the object and store the pointer. That requires a new
object type.
-->
我们只是初始化对象并存储指针。这需要一个新的对象类型。

^code obj-type-upvalue (1 before, 1 after)

<!--
And on the back side, a destructor-like function:
-->
背面则是类似析构的函数：

^code free-upvalue (3 before, 1 after)

<!--
Multiple closures can close over the same variable, so ObjUpvalue does not own
the variable it references. Thus, the only thing to free is the ObjUpvalue
itself.
-->
多个闭包可以关闭同一个变量，所以 ObjUpvalue 并不拥有它所引用的变量。因此，要释放的只有 ObjUpvalue 本身。

<!--
And, finally, to print:
-->
最后，是打印：

^code print-upvalue (3 before, 1 after)

<!--
Printing isn't useful to end users. Upvalues are objects only so that we can
take advantage of the VM's memory management. They aren't first-class values
that a Lox user can directly access in a program. So this code will never
actually execute... but it keeps the compiler from yelling at us about an
unhandled switch case, so here we are.
-->
打印对最终用户没什么用。上值之所以是对象，只是为了利用虚拟机的内存管理。它们不是 Lox 用户能在程序里直接访问的一等值。所以这段代码其实永远不会执行……但它能让编译器别因为未处理的 switch 分支冲我们嚷嚷，于是就这样吧。

<!--
-- Upvalues in closures
-->
### 闭包中的上值

<!--
When I first introduced upvalues, I said each closure has an array of them.
We've finally worked our way back to implementing that.
-->
我最初介绍上值时说过，每个闭包都有一个上值数组。我们终于绕回来实现它了。

^code upvalue-fields (1 before, 1 after)

<!--
<span name="count">Different</span> closures may have different numbers of
upvalues, so we need a dynamic array. The upvalues themselves are dynamically
allocated too, so we end up with a double pointer -- a pointer to a dynamically
allocated array of pointers to upvalues. We also store the number of elements in
the array.
-->
<span name="count">不同</span>闭包可能有不同数量的上值，所以我们需要动态数组。上值本身也是动态分配的，于是我们落得一个双重指针——指向一个动态分配的、装着指向上值的指针的数组。我们还存储数组中的元素个数。

<aside name="count">

<!--
Storing the upvalue count in the closure is redundant because the ObjFunction
that the ObjClosure references also keeps that count. As usual, this weird code
is to appease the GC. The collector may need to know an ObjClosure's upvalue
array size after the closure's corresponding ObjFunction has already been freed.
-->
把上值计数存在闭包里是多余的，因为 ObjClosure 引用的 ObjFunction 也保存着那计数。照例，这段怪代码是为了安抚 GC。收集器可能在闭包对应的 ObjFunction 已被释放之后，仍需要知道 ObjClosure 上值数组的大小。

</aside>

<!--
When we create an ObjClosure, we allocate an upvalue array of the proper size,
which we determined at compile time and stored in the ObjFunction.
-->
创建 ObjClosure 时，我们按合适大小分配上值数组——那大小在编译期就定好了，存在 ObjFunction 里。

^code allocate-upvalue-array (1 before, 1 after)

<!--
Before creating the closure object itself, we allocate the array of upvalues and
initialize them all to `NULL`. This weird ceremony around memory is a careful
dance to please the (forthcoming) garbage collection deities. It ensures the
memory manager never sees uninitialized memory.
-->
在创建闭包对象本身之前，我们分配上值数组并把它们全初始化为 `NULL`。这围绕内存的古怪仪式，是一场小心翼翼的舞蹈，好取悦（即将降临的）垃圾收集诸神。它确保内存管理器永远看不到未初始化的内存。

<!--
Then we store the array in the new closure, as well as copy the count over from
the ObjFunction.
-->
然后我们把数组存进新闭包，并把计数从 ObjFunction 拷过来。

^code init-upvalue-fields (1 before, 1 after)

<!--
When we free an ObjClosure, we also free the upvalue array.
-->
释放 ObjClosure 时，我们也释放上值数组。

^code free-upvalues (1 before, 1 after)

<!--
ObjClosure does not own the ObjUpvalue objects themselves, but it does own *the
array* containing pointers to those upvalues.
-->
ObjClosure 并不拥有 ObjUpvalue 对象本身，但它拥有装着指向那些上值的指针的*数组*。

<!--
We fill the upvalue array over in the interpreter when it creates a closure.
This is where we walk through all of the operands after `OP_CLOSURE` to see what
kind of upvalue each slot captures.
-->
我们在解释器创建闭包时填充上值数组。这里我们遍历 `OP_CLOSURE` 后面的全部操作数，看每个槽捕获的是哪种上值。

^code interpret-capture-upvalues (1 before, 1 after)

<!--
This code is the magic moment when a closure comes to life. We iterate over each
upvalue the closure expects. For each one, we read a pair of operand bytes. If
the upvalue closes over a local variable in the enclosing function, we let
`captureUpvalue()` do the work.
-->
这段代码是闭包活过来的魔法时刻。我们遍历闭包期望的每个上值。对每一个，读一对操作数字节。若上值关闭的是外围函数里的局部变量，就交给 `captureUpvalue()` 干活。

<!--
Otherwise, we capture an upvalue from the surrounding function. An `OP_CLOSURE`
instruction is emitted at the end of a function declaration. At the moment that
we are executing that declaration, the *current* function is the surrounding
one. That means the current function's closure is stored in the CallFrame at the
top of the callstack. So, to grab an upvalue from the enclosing function, we can
read it right from the `frame` local variable, which caches a reference to that
CallFrame.
-->
否则，我们从外围函数捕获一个上值。`OP_CLOSURE` 指令发在函数声明末尾。我们执行该声明的那一刻，*当前*函数就是外围那个。这意味着当前函数的闭包存在调用栈顶的 CallFrame 里。因此，要从外围函数抓取上值，可以直接从 `frame` 这个局部变量读——它缓存着对该 CallFrame 的引用。

<!--
Closing over a local variable is more interesting. Most of the work happens in a
separate function, but first we calculate the argument to pass to it. We need to
grab a pointer to the captured local's slot in the surrounding function's stack
window. That window begins at `frame->slots`, which points to slot zero. Adding
`index` offsets that to the local slot we want to capture. We pass that pointer
here:
-->
关闭局部变量更有意思。大部分工作在另一个函数里发生，但我们先算好要传给它的参数。我们需要拿到被捕获局部变量在外围函数栈窗口中那个槽的指针。那窗口从 `frame->slots` 开始，指向零号槽。加上 `index` 就偏移到我们想捕获的局部槽。我们把那指针传到这里：

^code capture-upvalue

<!--
This seems a little silly. All it does is create a new ObjUpvalue that captures
the given stack slot and returns it. Did we need a separate function for this?
Well, no, not *yet*. But you know we are going to end up sticking more code in
here.
-->
这显得有点傻。它只是创建一个捕获给定栈槽的新 ObjUpvalue 并返回。我们需要单独一个函数干这事吗？嗯，不，*暂时*不。但你知道我们最终会往这儿塞更多代码。

<!--
First, let's wrap up what we're working on. Back in the interpreter code for
handling `OP_CLOSURE`, we eventually finish iterating through the upvalue
array and initialize each one. When that completes, we have a new closure with
an array full of upvalues pointing to variables.
-->
先把正在做的收尾。回到处理 `OP_CLOSURE` 的解释器代码，我们最终会遍历完上值数组并初始化每一个。完成后，我们就有了一个新闭包，数组里装满指向变量的上值。

<!--
With that in hand, we can implement the instructions that work with those
upvalues.
-->
有了这些，我们就能实现与那些上值打交道的指令。

^code interpret-get-upvalue (1 before, 1 after)

<!--
The operand is the index into the current function's upvalue array. So we simply
look up the corresponding upvalue and dereference its location pointer to read
the value in that slot. Setting a variable is similar.
-->
操作数是当前函数上值数组中的下标。于是我们只需查找对应上值，解引用其 location 指针，读出那个槽里的值。设置变量与此类似。

^code interpret-set-upvalue (1 before, 1 after)

<!--
We <span name="assign">take</span> the value on top of the stack and store it
into the slot pointed to by the chosen upvalue. Just as with the instructions
for local variables, it's important that these instructions are fast. User
programs are constantly reading and writing variables, so if that's slow,
everything is slow. And, as usual, the way we make them fast is by keeping them
simple. These two new instructions are pretty good: no control flow, no complex
arithmetic, just a couple of pointer indirections and a `push()`.
-->
我们<span name="assign">取</span>栈顶的值，存进所选上值指向的那个槽。和局部变量指令一样，这些指令必须快，这很重要。用户程序不停读写变量，这儿一慢，一切都慢。照例，让它们快的办法是保持简单。这两条新指令相当不错：没有控制流，没有复杂算术，只是几次指针间接和一个 `push()`。

<aside name="assign">

<!--
The set instruction doesn't *pop* the value from the stack because, remember,
assignment is an expression in Lox. So the result of the assignment -- the
assigned value -- needs to remain on the stack for the surrounding expression.
-->
set 指令并不从栈上*弹出*那个值，因为——记住——在 Lox 里赋值是表达式。所以赋值的结果——被赋的那个值——需要留在栈上，供外围表达式使用。

</aside>

<!--
This is a milestone. As long as all of the variables remain on the stack, we
have working closures. Try this:
-->
这是一个里程碑。只要所有变量仍留在栈上，我们就有能工作的闭包。试试这个：

```lox
fun outer() {
  var x = "outside";
  fun inner() {
    print x;
  }
  inner();
}
outer();
```

<!--
Run this, and it correctly prints "outside".
-->
跑起来，它正确地打印 `"outside"`。

<!--
-- Closed Upvalues
-->
## 已关闭的上值

<!--
Of course, a key feature of closures is that they hold on to the variable as
long as needed, even after the function that declares the variable has returned.
Here's another example that *should* work:
-->
当然，闭包的一个关键特性是：它们按需抓住变量不放，即便声明该变量的函数已经返回。这儿是另一个*应当*能工作的例子：

```lox
fun outer() {
  var x = "outside";
  fun inner() {
    print x;
  }

  return inner;
}

var closure = outer();
closure();
```

<!--
But if you run it right now... who knows what it does? At runtime, it will end
up reading from a stack slot that no longer contains the closed-over variable.
Like I've mentioned a few times, the crux of the issue is that variables in
closures don't have stack semantics. That means we've got to hoist them off the
stack when the function where they were declared returns. This final section of
the chapter does that.
-->
但若你现在就跑……谁知道它会干什么？运行时，它最终会从一个已经不再装着被关闭变量的栈槽里读。如我提过几次的，问题的症结在于：闭包里的变量没有栈语义。这意味着，声明它们的函数返回时，我们得把它们从栈上抬走。本章最后这一节就干这事。

<!--
-- Values and variables
-->
### 值与变量

<!--
Before we get to writing code, I want to dig into an important semantic point.
Does a closure close over a *value* or a *variable?* This isn't purely an <span
name="academic">academic</span> question. I'm not just splitting hairs.
Consider:
-->
动手写代码之前，我想挖一个重要的语义点。闭包关闭的是*值*还是*变量*？这不全是<span name="academic">学究</span>式的问题。我可不是在抠字眼。想想：

<aside name="academic">

<!--
If Lox didn't allow assignment, it *would* be an academic question.
-->
若 Lox 不允许赋值，那*就会*是个学究问题。

</aside>

```lox
var globalSet;
var globalGet;

fun main() {
  var a = "initial";

  fun set() { a = "updated"; }
  fun get() { print a; }

  globalSet = set;
  globalGet = get;
}

main();
globalSet();
globalGet();
```

<!--
The outer `main()` function creates two closures and stores them in <span
name="global">global</span> variables so that they outlive the execution of
`main()` itself. Both of those closures capture the same variable. The first
closure assigns a new value to it and the second closure reads the variable.
-->
外层的 `main()` 创建两个闭包，并把它们存进<span name="global">全局</span>变量，好让它们比 `main()` 本身的执行活得更久。两个闭包都捕获同一个变量。第一个闭包给它赋新值，第二个闭包读该变量。

<aside name="global">

<!--
The fact that I'm using a couple of global variables isn't significant. I needed
some way to return two values from a function, and without any kind of
collection type in Lox, my options were limited.
-->
我用了一对全局变量，这本身并不重要。我需要某种办法从函数返回两个值，而 Lox 没有任何集合类型，选择很有限。

</aside>

<!--
What does the call to `globalGet()` print? If closures capture *values* then
each closure gets its own copy of `a` with the value that `a` had at the point
in time that the closure's function declaration executed. The call to
`globalSet()` will modify `set()`'s copy of `a`, but `get()`'s copy will be
unaffected. Thus, the call to `globalGet()` will print "initial".
-->
对 `globalGet()` 的调用打印什么？若闭包捕获的是*值*，则每个闭包各自得到一份 `a` 的拷贝，值是闭包的函数声明执行那一刻 `a` 所具有的值。对 `globalSet()` 的调用会修改 `set()` 那份 `a`，但 `get()` 那份不受影响。于是对 `globalGet()` 的调用会打印 `"initial"`。

<!--
If closures close over variables, then `get()` and `set()` will both capture --
reference -- the *same mutable variable*. When `set()` changes `a`, it changes
the same `a` that `get()` reads from. There is only one `a`. That, in turn,
implies the call to `globalGet()` will print "updated".
-->
若闭包关闭的是变量，则 `get()` 和 `set()` 都会捕获——引用——*同一个可变变量*。当 `set()` 改 `a` 时，它改的就是 `get()` 所读的那个 `a`。只有一个 `a`。这进而意味着对 `globalGet()` 的调用会打印 `"updated"`。

<!--
Which is it? The answer for Lox and most other languages I know with closures is
the latter. Closures capture variables. You can think of them as capturing *the
place the value lives*. This is important to keep in mind as we deal with
closed-over variables that are no longer on the stack. When a variable moves to
the heap, we need to ensure that all closures capturing that variable retain a
reference to its *one* new location. That way, when the variable is mutated, all
closures see the change.
-->
到底是哪一种？对 Lox 以及我知道的大多数带闭包的语言，答案是后者。闭包捕获变量。你可以想成它们捕获的是*值所住的那个地方*。处理已不在栈上的被关闭变量时，这一点要记牢。变量移到堆上时，我们需要确保所有捕获该变量的闭包都保留对其*唯一*新位置的引用。这样，变量被修改时，所有闭包都能看见变化。

<!--
-- Closing upvalues
-->
### 关闭上值

<!--
We know that local variables always start out on the stack. This is faster, and
lets our single-pass compiler emit code before it discovers the variable has
been captured. We also know that closed-over variables need to move to the heap
if the closure outlives the function where the captured variable is declared.
-->
我们知道局部变量总是从栈上起步。这样更快，也让我们的单遍编译器能在发现变量被捕获之前就发出代码。我们也知道：若闭包比声明被捕获变量的函数活得更久，被关闭的变量就需要移到堆上。

<!--
Following Lua, we'll use **open upvalue** to refer to an upvalue that points to
a local variable still on the stack. When a variable moves to the heap, we are
*closing* the upvalue and the result is, naturally, a **closed upvalue**. The
two questions we need to answer are:
-->
沿用 Lua，我们用**开放上值（open upvalue）**指仍指向栈上局部变量的上值。变量移到堆上时，我们是在*关闭*上值，结果自然就是**已关闭的上值（closed upvalue）**。需要回答的两个问题是：

<!--
1.  Where on the heap does the closed-over variable go?

2.  When do we close the upvalue?
-->
1.  被关闭的变量在堆上的什么地方？

2.  我们何时关闭上值？

<!--
The answer to the first question is easy. We already have a convenient object on
the heap that represents a reference to a variable -- ObjUpvalue itself. The
closed-over variable will move into a new field right inside the ObjUpvalue
struct. That way we don't need to do any additional heap allocation to close an
upvalue.
-->
第一个问题的答案很容易。我们堆上已有一个方便的对象表示对变量的引用——ObjUpvalue 本身。被关闭的变量会移进 ObjUpvalue 结构体内部的一个新字段。这样关闭上值时不必再做额外的堆分配。

<!--
The second question is straightforward too. As long as the variable is on the
stack, there may be code that refers to it there, and that code must work
correctly. So the logical time to hoist the variable to the heap is as late as
possible. If we move the local variable right when it goes out of scope, we are
certain that no code after that point will try to access it from the stack.
<span name="after">After</span> the variable is out of scope, the compiler will
have reported an error if any code tried to use it.
-->
第二个问题也很直截了当。只要变量还在栈上，就可能有代码在那儿引用它，那些代码必须正确工作。因此，把变量抬到堆上的合乎逻辑的时机，是尽可能晚。若我们在局部变量刚退出作用域时就移动它，就能确定那一点之后不会再有代码试图从栈上访问它。变量出了作用域<span name="after">之后</span>，若还有代码试图使用它，编译器早就报错了。

<aside name="after">

<!--
By "after" here, I mean in the lexical or textual sense -- code past the `}`
for the block containing the declaration of the closed-over variable.
-->
此处的“之后”，我指的是词法或文本意义上的——越过包含被关闭变量声明的那个块的 `}` 之后的代码。

</aside>

<!--
The compiler already emits an `OP_POP` instruction when a local variable goes
out of scope. If a variable is captured by a closure, we will instead emit a
different instruction to hoist that variable out of the stack and into its
corresponding upvalue. To do that, the compiler needs to know which <span
name="param">locals</span> are closed over.
-->
局部变量退出作用域时，编译器已会发出 `OP_POP` 指令。若变量被闭包捕获，我们改为发出另一条指令，把该变量从栈上抬进对应的上值。为此，编译器需要知道哪些<span name="param">局部变量</span>被关闭了。

<aside name="param">

<!--
The compiler doesn't pop parameters and locals declared immediately inside the
body of a function. We'll handle those too, in the runtime.
-->
编译器并不弹出参数和紧挨着声明在函数体里的局部变量。那些我们也会处理——在运行时。

</aside>

<!--
The compiler already maintains an array of Upvalue structs for each local
variable in the function to track exactly that state. That array is good for
answering "Which variables does this closure use?" But it's poorly suited for
answering, "Does *any* function capture this local variable?" In particular,
once the Compiler for some closure has finished, the Compiler for the enclosing
function whose variable has been captured no longer has access to any of the
upvalue state.
-->
编译器已为函数里的每个局部变量维护一个 Upvalue 结构数组，正是为了追踪那状态。那数组擅长回答“这个闭包用了哪些变量？”，却拙于回答“*有没有任何*函数捕获了这个局部变量？”尤其是，某个闭包的 Compiler 一旦结束，被捕获变量所在的外围函数的 Compiler 就再也访问不到任何上值状态了。

<!--
In other words, the compiler maintains pointers from upvalues to the locals they
capture, but not in the other direction. So we first need to add some extra
tracking inside the existing Local struct so that we can tell if a given local
is captured by a closure.
-->
换句话说，编译器维护着从上值到它们所捕获的局部变量的指针，却没有反向的。所以我们首先要在现有的 Local 结构里加些额外追踪，好判断某个给定局部是否被闭包捕获。

^code is-captured-field (1 before, 1 after)

<!--
This field is `true` if the local is captured by any later nested function
declaration. Initially, all locals are not captured.
-->
若该局部被任何后续嵌套函数声明捕获，这字段为 `true`。起初，所有局部都未被捕获。

^code init-is-captured (1 before, 1 after)

<!--
<span name="zero">Likewise</span>, the special "slot zero local" that the
compiler implicitly declares is not captured.
-->
<span name="zero">同样</span>，编译器隐式声明的那个特殊“零号槽局部”也未被捕获。

<aside name="zero">

<!--
Later in the book, it *will* become possible for a user to capture this
variable. Just building some anticipation here.
-->
本书后面，用户*将*能够捕获这个变量。这儿先埋点期待。

</aside>

^code init-zero-local-is-captured (1 before, 1 after)

<!--
When resolving an identifier, if we end up creating an upvalue for a local
variable, we mark it as captured.
-->
解析标识符时，若最终为某个局部变量创建了上值，就把它标为已捕获。

^code mark-local-captured (1 before, 1 after)

<!--
Now, at the end of a block scope when the compiler emits code to free the stack
slots for the locals, we can tell which ones need to get hoisted onto the heap.
We'll use a new instruction for that.
-->
现在，在块作用域末尾、编译器发出代码释放局部变量的栈槽时，我们能分辨哪些需要抬到堆上。我们用一条新指令干这事。

^code end-scope (3 before, 2 after)

<!--
The instruction requires no operand. We know that the variable will always be
right on top of the stack at the point that this instruction executes. We
declare the instruction.
-->
这条指令不需要操作数。我们知道执行该指令时，变量总在栈顶。我们声明这条指令。

^code close-upvalue-op (1 before, 1 after)

<!--
And add trivial disassembler support for it:
-->
并给它加上琐碎的反汇编支持：

^code disassemble-close-upvalue (1 before, 1 after)

<!--
Excellent. Now the generated bytecode tells the runtime exactly when each
captured local variable must move to the heap. Better, it does so only for the
locals that *are* used by a closure and need this special treatment. This aligns
with our general performance goal that we want users to pay only for
functionality that they use. Variables that aren't used by closures live and die
entirely on the stack just as they did before.
-->
好极了。现在生成的字节码精确地告诉运行时，每个被捕获的局部变量何时必须移到堆上。更好的是，它只对*确实*被闭包使用、需要这特殊待遇的局部这么做。这符合我们总的性能目标：用户只为用到的功能付账。不被闭包使用的变量，仍完全在栈上生灭，一如既往。

<!--
-- Tracking open upvalues
-->
### 追踪开放的上值

<!--
Let's move over to the runtime side. Before we can interpret `OP_CLOSE_UPVALUE`
instructions, we have an issue to resolve. Earlier, when I talked about whether
closures capture variables or values, I said it was important that if multiple
closures access the same variable that they end up with a reference to the
exact same storage location in memory. That way if one closure writes to the
variable, the other closure sees the change.
-->
转到运行时这一侧。在能解释 `OP_CLOSE_UPVALUE` 指令之前，还有一个问题要解决。先前谈到闭包捕获的是变量还是值时，我说：若多个闭包访问同一变量，它们最终必须引用内存中完全相同的存储位置，这一点很重要。这样，一个闭包写入变量时，另一个闭包能看见变化。

<!--
Right now, if two closures capture the same <span name="indirect">local</span>
variable, the VM creates a separate Upvalue for each one. The necessary sharing
is missing. When we move the variable off the stack, if we move it into only one
of the upvalues, the other upvalue will have an orphaned value.
-->
眼下，若两个闭包捕获同一个<span name="indirect">局部</span>变量，虚拟机会为各自创建一个单独的 Upvalue。必要的共享缺失了。把变量移出栈时，若只移进其中一个上值，另一个上值就会落得一个孤儿值。

<aside name="indirect">

<!--
The VM *does* share upvalues if one closure captures an *upvalue* from a
surrounding function. The nested case works correctly. But if two *sibling*
closures capture the same local variable, they each create a separate
ObjUpvalue.
-->
若一个闭包从外围函数捕获一个*上值*，虚拟机*确实*会共享上值。嵌套情形工作正常。但若两个*兄弟*闭包捕获同一局部变量，它们会各自创建一个 ObjUpvalue。

</aside>

<!--
To fix that, whenever the VM needs an upvalue that captures a particular local
variable slot, we will first search for an existing upvalue pointing to that
slot. If found, we reuse that. The challenge is that all of the previously
created upvalues are squirreled away inside the upvalue arrays of the various
closures. Those closures could be anywhere in the VM's memory.
-->
要修好这点：每当虚拟机需要一个捕获特定局部变量槽的上值时，我们先搜索是否已有指向该槽的上值。若找到，就复用它。难点在于，先前创建的所有上值都藏在各个闭包的上值数组里。那些闭包可能在虚拟机内存的任何地方。

<!--
The first step is to give the VM its own list of all open upvalues that point to
variables still on the stack. Searching a list each time the VM needs an upvalue
sounds like it might be slow, but in practice, it's not bad. The number of
variables on the stack that actually get closed over tends to be small. And
function declarations that <span name="create">create</span> closures are rarely
on performance critical execution paths in the user's program.
-->
第一步是给虚拟机自己一份列表，列出所有仍指向栈上变量的开放上值。每次需要上值都搜一遍列表，听起来可能慢，但实践中并不差。栈上真正被关闭的变量通常不多。而<span name="create">创建</span>闭包的函数声明，很少落在用户程序性能关键的执行路径上。

<aside name="create">

<!--
Closures are frequently *invoked* inside hot loops. Think about the closures
passed to typical higher-order functions on collections like [`map()`][map] and
[`filter()`][filter]. That should be fast. But the function declaration that
*creates* the closure happens only once and is usually outside of the loop.

[map]: https://en.wikipedia.org/wiki/Map_(higher-order_function)
[filter]: https://en.wikipedia.org/wiki/Filter_(higher-order_function)
-->
闭包在热循环里被*调用*的情况很常见。想想传给集合上典型高阶函数——如 [`map()`][map] 和 [`filter()`][filter]——的那些闭包。那应当很快。但*创建*闭包的函数声明只发生一次，而且通常在循环之外。

[map]: https://en.wikipedia.org/wiki/Map_(higher-order_function)
[filter]: https://en.wikipedia.org/wiki/Filter_(higher-order_function)

</aside>

<!--
Even better, we can order the list of open upvalues by the stack slot index they
point to. The common case is that a slot has *not* already been captured --
sharing variables between closures is uncommon -- and closures tend to capture
locals near the top of the stack. If we store the open upvalue array in stack
slot order, as soon as we step past the slot where the local we're capturing
lives, we know it won't be found. When that local is near the top of the stack,
we can exit the loop pretty early.
-->
更好的是，我们可以按它们指向的栈槽下标给开放上值列表排序。常见情形是某个槽*尚未*被捕获——闭包之间共享变量并不常见——而且闭包往往捕获靠近栈顶的局部变量。若按栈槽顺序存放开放上值列表，一旦走过我们正捕获的那个局部所在的槽，就知道找不到了。当那个局部靠近栈顶时，我们可以相当早地退出循环。

<!--
Maintaining a sorted list requires inserting elements in the middle efficiently.
That suggests using a linked list instead of a dynamic array. Since we defined
the ObjUpvalue struct ourselves, the easiest implementation is an intrusive list
that puts the next pointer right inside the ObjUpvalue struct itself.
-->
维护有序列表需要高效地在中间插入元素。这暗示用链表而不是动态数组。既然 ObjUpvalue 结构是我们自己定义的，最容易的实现是侵入式链表，把 next 指针直接放进 ObjUpvalue 结构体本身。

^code next-field (1 before, 1 after)

<!--
When we allocate an upvalue, it is not attached to any list yet so the link is
`NULL`.
-->
分配上值时，它尚未挂到任何列表上，所以链接是 `NULL`。

^code init-next (1 before, 1 after)

<!--
The VM owns the list, so the head pointer goes right inside the main VM struct.
-->
列表归虚拟机所有，所以头指针就放在主 VM 结构体里。

^code open-upvalues-field (1 before, 1 after)

<!--
The list starts out empty.
-->
列表起初为空。

^code init-open-upvalues (1 before, 1 after)

<!--
Starting with the first upvalue pointed to by the VM, each open upvalue points
to the next open upvalue that references a local variable farther down the
stack. This script, for example,
-->
从虚拟机指向的第一个上值开始，每个开放上值指向下一个引用更靠下栈上局部变量的开放上值。例如这个脚本，

```lox
{
  var a = 1;
  fun f() {
    print a;
  }
  var b = 2;
  fun g() {
    print b;
  }
  var c = 3;
  fun h() {
    print c;
  }
}
```

<!--
should produce a series of linked upvalues like so:
-->
应产生一串像这样链接起来的上值：

<img src="image/closures/linked-list.png" alt="Three upvalues in a linked list."/>

<!--
Whenever we close over a local variable, before creating a new upvalue, we look
for an existing one in the list.
-->
每当关闭一个局部变量时，在创建新上值之前，我们先在列表里找有没有已有的。

^code look-for-existing-upvalue (1 before, 1 after)

<!--
We start at the <span name="head">head</span> of the list, which is the upvalue
closest to the top of the stack. We walk through the list, using a little
pointer comparison to iterate past every upvalue pointing to slots above the one
we're looking for. While we do that, we keep track of the preceding upvalue on
the list. We'll need to update that node's `next` pointer if we end up inserting
a node after it.
-->
我们从列表的<span name="head">头</span>开始，那是最靠近栈顶的上值。我们遍历列表，用一点指针比较，跳过所有指向我们正在找的槽之上的上值。同时记下列表上的前一个上值。若最终在它后面插入节点，就需要更新那个节点的 `next` 指针。

<aside name="head">

<!--
It's a singly linked list. It's not like we have any other choice than to start
at the head and go forward from there.
-->
这是单链表。除了从头开始往前走，我们也没什么别的选择。

</aside>

<!--
There are three reasons we can exit the loop:
-->
我们可能因三种原因退出循环：

<!--
1.  **The local slot we stopped at *is* the slot we're looking for.** We found
    an existing upvalue capturing the variable, so we reuse that upvalue.

2.  **We ran out of upvalues to search.** When `upvalue` is `NULL`, it means
    every open upvalue in the list points to locals above the slot we're looking
    for, or (more likely) the upvalue list is empty. Either way, we didn't find
    an upvalue for our slot.

3.  **We found an upvalue whose local slot is *below* the one we're looking
    for.** Since the list is sorted, that means we've gone past the slot we are
    closing over, and thus there must not be an existing upvalue for it.
-->
1.  **我们停在的局部槽*正是*要找的那个槽。** 找到了捕获该变量的已有上值，于是复用它。

2.  **要搜的上值用尽了。** 当 `upvalue` 为 `NULL` 时，意味着列表里每个开放上值都指向我们要找的槽之上的局部，或者（更可能）上值列表为空。无论哪种，都没找到我们这个槽的上值。

3.  **找到一个局部槽*低于*我们要找的那个的上值。** 既然列表有序，这意味着我们已经走过正在关闭的那个槽，因而必定没有已有上值。

<!--
In the first case, we're done and we've returned. Otherwise, we create a new
upvalue for our local slot and insert it into the list at the right location.
-->
第一种情形下，我们做完并已返回。否则，为我们的局部槽创建一个新上值，并在正确位置插入列表。

^code insert-upvalue-in-list (1 before, 1 after)

<!--
The current incarnation of this function already creates the upvalue, so we only
need to add code to insert the upvalue into the list. We exited the list
traversal by either going past the end of the list, or by stopping on the first
upvalue whose stack slot is below the one we're looking for. In either case,
that means we need to insert the new upvalue *before* the object pointed at by
`upvalue` (which may be `NULL` if we hit the end of the list).
-->
这个函数当前的样子已经会创建上值，所以我们只需加代码把它插入列表。我们退出列表遍历，要么是走过了列表末尾，要么是停在第一个栈槽低于我们要找的上值上。无论哪种，都意味着要把新上值插在 `upvalue` 指向的对象*之前*（若撞到列表末尾，它可能是 `NULL`）。

<!--
As you may have learned in Data Structures 101, to insert a node into a linked
list, you set the `next` pointer of the previous node to point to your new one.
We have been conveniently keeping track of that preceding node as we walked the
list. We also need to handle the <span name="double">special</span> case where
we are inserting a new upvalue at the head of the list, in which case the "next"
pointer is the VM's head pointer.
-->
正如你在数据结构入门课里可能学过的，往链表插节点时，要把前一个节点的 `next` 指针指向新节点。我们在走列表时已经方便地记着那个前驱节点。还要处理在列表头插入新上值的<span name="double">特殊</span>情形——那时“next”指针就是虚拟机的头指针。

<aside name="double">

<!--
There is a shorter implementation that handles updating either the head pointer
or the previous upvalue's `next` pointer uniformly by using a pointer to a
pointer, but that kind of code confuses almost everyone who hasn't reached some
Zen master level of pointer expertise. I went with the basic `if` statement
approach.
-->
有一种更短的实现，用指向指针的指针，统一处理更新头指针或前一个上值的 `next` 指针；但那种代码会把几乎所有还没达到某种指针禅宗大师境界的人弄糊涂。我选了基本的 `if` 语句做法。

</aside>

<!--
With this updated function, the VM now ensures that there is only ever a single
ObjUpvalue for any given local slot. If two closures capture the same variable,
they will get the same upvalue. We're ready to move those upvalues off the
stack now.
-->
有了这个更新后的函数，虚拟机现在确保任意给定局部槽永远只有一个 ObjUpvalue。若两个闭包捕获同一变量，它们会得到同一个上值。我们准备好把那些上值移出栈了。

<!--
-- Closing upvalues at runtime
-->
### 在运行时关闭上值

<!--
The compiler helpfully emits an `OP_CLOSE_UPVALUE` instruction to tell the VM
exactly when a local variable should be hoisted onto the heap. Executing that
instruction is the interpreter's responsibility.
-->
编译器体贴地发出 `OP_CLOSE_UPVALUE` 指令，精确告诉虚拟机何时该把局部变量抬到堆上。执行那条指令是解释器的责任。

^code interpret-close-upvalue (1 before, 1 after)

<!--
When we reach the instruction, the variable we are hoisting is right on top of
the stack. We call a helper function, passing the address of that stack slot.
That function is responsible for closing the upvalue and moving the local from
the stack to the heap. After that, the VM is free to discard the stack slot,
which it does by calling `pop()`.
-->
到达该指令时，我们正抬起的变量就在栈顶。我们调用一个辅助函数，传入那个栈槽的地址。该函数负责关闭上值，并把局部从栈移到堆。之后，虚拟机可以丢弃那个栈槽——它通过调用 `pop()` 来做。

<!--
The fun stuff happens here:
-->
好玩的部分在这里：

^code close-upvalues

<!--
This function takes a pointer to a stack slot. It closes every open upvalue it
can find that points to that slot or any slot above it on the stack. Right now,
we pass a pointer only to the top slot on the stack, so the "or above it" part
doesn't come into play, but it will soon.
-->
这个函数接受指向栈槽的指针。它关闭能找到的、指向该槽或栈上任何更高槽的每一个开放上值。眼下我们只传入栈顶槽的指针，所以“或之上”那部分还没派上用场，但很快就会。

<!--
To do this, we walk the VM's list of open upvalues, again from top to bottom. If
an upvalue's location points into the range of slots we're closing, we close the
upvalue. Otherwise, once we reach an upvalue outside of the range, we know the
rest will be too, so we stop iterating.
-->
为此，我们再次自上而下走虚拟机的开放上值列表。若某个上值的 location 指向我们正在关闭的槽范围，就关闭它。否则，一旦到达范围外的上值，就知道其余也都在外，于是停止迭代。

<!--
The way an upvalue gets closed is pretty <span name="cool">cool</span>. First,
we copy the variable's value into the `closed` field in the ObjUpvalue. That's
where closed-over variables live on the heap. The `OP_GET_UPVALUE` and
`OP_SET_UPVALUE` instructions need to look for the variable there after it's
been moved. We could add some conditional logic in the interpreter code for
those instructions to check some flag for whether the upvalue is open or closed.
-->
上值被关闭的方式相当<span name="cool">酷</span>。首先，把变量的值拷进 ObjUpvalue 的 `closed` 字段。那就是被关闭变量在堆上的住所。`OP_GET_UPVALUE` 和 `OP_SET_UPVALUE` 在变量移走后需要到那儿去找。我们可以在那些指令的解释器代码里加些条件逻辑，检查某个标志看上值是开放还是已关闭。

<!--
But there is already a level of indirection in play -- those instructions
dereference the `location` pointer to get to the variable's value. When the
variable moves from the stack to the `closed` field, we simply update that
`location` to the address of the ObjUpvalue's *own* `closed` field.
-->
但已经有一层间接在起作用——那些指令解引用 `location` 指针以到达变量的值。变量从栈移到 `closed` 字段时，我们只需把 `location` 更新为 ObjUpvalue *自己的* `closed` 字段的地址。

<aside name="cool">

<!--
I'm not praising myself here. This is all the Lua dev team's innovation.
-->
我这儿可不是在夸自己。这全是 Lua 开发团队的创新。

</aside>

<img src="image/closures/closing.png" alt="Moving a value from the stack to the upvalue's 'closed' field and then pointing the 'value' field to it."/>

<!--
We don't need to change how `OP_GET_UPVALUE` and `OP_SET_UPVALUE` are
interpreted at all. That keeps them simple, which in turn keeps them fast. We do
need to add the new field to ObjUpvalue, though.
-->
我们完全不必改 `OP_GET_UPVALUE` 和 `OP_SET_UPVALUE` 的解释方式。这让它们保持简单，进而保持快速。不过我们确实需要给 ObjUpvalue 加上新字段。

^code closed-field (1 before, 1 after)

<!--
And we should zero it out when we create an ObjUpvalue so there's no
uninitialized memory floating around.
-->
创建 ObjUpvalue 时应把它清零，好让未初始化的内存别到处飘。

^code init-closed (1 before, 1 after)

<!--
Whenever the compiler reaches the end of a block, it discards all local
variables in that block and emits an `OP_CLOSE_UPVALUE` for each local variable
that was closed over. The compiler <span name="close">does</span> *not* emit any
instructions at the end of the outermost block scope that defines a function
body. That scope contains the function's parameters and any locals declared
immediately inside the function. Those need to get closed too.
-->
每当编译器到达块的末尾，它丢弃该块中所有局部变量，并为每个被关闭的局部变量发出 `OP_CLOSE_UPVALUE`。编译器在定义函数体的最外层块作用域末尾<span name="close">并</span>*不*发出任何指令。那个作用域装着函数的参数以及紧挨着声明在函数里的局部。那些也需要被关闭。

<aside name="close">

<!--
There's nothing *preventing* us from closing the outermost function scope in the
compiler and emitting `OP_POP` and `OP_CLOSE_UPVALUE` instructions. Doing so is
just unnecessary because the runtime discards all of the stack slots used by the
function implicitly when it pops the call frame.
-->
并没有什么*阻止*我们在编译器里关闭最外层函数作用域并发出 `OP_POP` 和 `OP_CLOSE_UPVALUE`。这么做只是没必要，因为运行时在弹出调用帧时会隐式丢弃该函数用过的全部栈槽。

</aside>

<!--
This is the reason `closeUpvalues()` accepts a pointer to a stack slot. When a
function returns, we call that same helper and pass in the first stack slot
owned by the function.
-->
这就是 `closeUpvalues()` 接受栈槽指针的原因。函数返回时，我们调用同一个辅助函数，传入该函数拥有的第一个栈槽。

^code return-close-upvalues (1 before, 1 after)

<!--
By passing the first slot in the function's stack window, we close every
remaining open upvalue owned by the returning function. And with that, we now
have a fully functioning closure implementation. Closed-over variables live as
long as they are needed by the functions that capture them.
-->
传入函数栈窗口的第一个槽，我们就关闭了返回函数仍拥有的每一个开放上值。至此，我们有了完整可用的闭包实现。被关闭的变量只要仍被捕获它们的函数需要，就会一直活着。

<!--
This was a lot of work! In jlox, closures fell out naturally from our
environment representation. In clox, we had to add a lot of code -- new bytecode
instructions, more data structures in the compiler, and new runtime objects. The
VM very much treats variables in closures as different from other variables.
-->
活儿可不少！在 jlox 里，闭包从我们的环境表示里自然长出来。在 clox 里，我们得加大量代码——新的字节码指令、编译器里更多数据结构，以及新的运行时对象。虚拟机对待闭包里的变量，与对待其他变量大不相同。

<!--
There is a rationale for that. In terms of implementation complexity, jlox gave
us closures "for free". But in terms of *performance*, jlox's closures are
anything but. By allocating *all* environments on the heap, jlox pays a
significant performance price for *all* local variables, even the majority which
are never captured by closures.
-->
这是有道理的。就实现复杂度而言，jlox 让我们“白得”了闭包。但就*性能*而言，jlox 的闭包可一点都不白。把*所有*环境都分配在堆上，jlox 为*所有*局部变量都付出了可观的性能代价，即便其中大多数从未被闭包捕获。

<!--
With clox, we have a more complex system, but that allows us to tailor the
implementation to fit the two use patterns we observe for local variables. For
most variables which do have stack semantics, we allocate them entirely on the
stack which is simple and fast. Then, for the few local variables where that
doesn't work, we have a second slower path we can opt in to as needed.
-->
有了 clox，我们有了一套更复杂的系统，但这让我们能按观察到的局部变量两种用法来定制实现。对大多数确实具有栈语义的变量，我们完全在栈上分配，简单又快。然后，对那少数栈行不通的局部变量，我们有第二条较慢的路径，按需选用。

<!--
Fortunately, users don't perceive the complexity. From their perspective, local
variables in Lox are simple and uniform. The *language itself* is as simple as
jlox's implementation. But under the hood, clox is watching what the user does
and optimizing for their specific uses. As your language implementations grow in
sophistication, you'll find yourself doing this more. A large fraction of
"optimization" is about adding special case code that detects certain uses and
provides a custom-built, faster path for code that fits that pattern.
-->
幸好用户察觉不到这份复杂。从他们的角度看，Lox 里的局部变量简单而统一。*语言本身*和 jlox 的实现一样简单。但在引擎盖下，clox 正盯着用户在做什么，并为他们的具体用法做优化。随着你的语言实现越来越精致，你会发现自己越来越多地这么做。很大一部分“优化”，就是加上检测某些用法的特例代码，并为契合那模式的代码提供量身打造的更快路径。

<!--
We have lexical scoping fully working in clox now, which is a major milestone.
And, now that we have functions and variables with complex lifetimes, we also
have a *lot* of objects floating around in clox's heap, with a web of pointers
stringing them together. The [next step][] is figuring out how to manage that
memory so that we can free some of those objects when they're no longer needed.
-->
词法作用域如今在 clox 里完全跑通了，这是一个重大里程碑。而且，既有了寿命复杂的函数与变量，clox 的堆上也就漂着*大量*对象，由一张指针网把它们串在一起。[下一步][next step]是弄清如何管理那份内存，好在对象不再需要时释放其中一些。

[next step]: garbage-collection.html

<div class="challenges">

<!--
-- Challenges
-->
## 挑战

<!--
1.  Wrapping every ObjFunction in an ObjClosure introduces a level of
    indirection that has a performance cost. That cost isn't necessary for
    functions that do not close over any variables, but it does let the runtime
    treat all calls uniformly.

    Change clox to only wrap functions in ObjClosures that need upvalues. How
    does the code complexity and performance compare to always wrapping
    functions? Take care to benchmark programs that do and do not use closures.
    How should you weight the importance of each benchmark? If one gets slower
    and one faster, how do you decide what trade-off to make to choose an
    implementation strategy?
-->
1.  把每个 ObjFunction 都包进 ObjClosure，引入了一层有性能代价的间接。对并不关闭任何变量的函数，这代价并非必要，但它让运行时能统一对待所有调用。

    改 clox，只把需要上值的函数包进 ObjClosure。代码复杂度与性能，和始终包装函数相比如何？务必基准测试既使用也不使用闭包的程序。你该如何权衡每个基准的重要性？若一个变慢、一个变快，你如何决定取舍，以选定实现策略？

<!--
2.  Read the design note below. I'll wait. Now, how do you think Lox *should*
    behave? Change the implementation to create a new variable for each loop
    iteration.
-->
2.  读下面的设计笔记。我等着。现在，你认为 Lox *应当*如何表现？改实现，让每次循环迭代都创建新变量。

<!--
3.  A [famous koan][koan] teaches us that "objects are a poor man's closure"
    (and vice versa). Our VM doesn't support objects yet, but now that we have
    closures we can approximate them. Using closures, write a Lox program that
    models two-dimensional vector "objects". It should:

    *   Define a "constructor" function to create a new vector with the given
        *x* and *y* coordinates.

    *   Provide "methods" to access the *x* and *y* coordinates of values
        returned from that constructor.

    *   Define an addition "method" that adds two vectors and produces a third.


[koan]: http://wiki.c2.com/?ClosuresAndObjectsAreEquivalent
-->
3.  一则[著名公案][koan]教导我们：“对象是穷人的闭包”（反之亦然）。我们的虚拟机还不支持对象，但既有了闭包，就可以近似它们。用闭包写一个 Lox 程序，建模二维向量“对象”。它应当：

    *   定义一个“构造函数”，用给定的 *x* 和 *y* 坐标创建新向量。

    *   提供“方法”，访问从该构造函数返回的值的 *x* 和 *y* 坐标。

    *   定义一个加法“方法”，把两个向量相加并产生第三个。

[koan]: http://wiki.c2.com/?ClosuresAndObjectsAreEquivalent

</div>

<div class="design-note">

<!--
-- Design Note: Closing Over the Loop Variable
-->
## 设计笔记：关闭循环变量

<!--
Closures capture variables. When two closures capture the same variable, they
share a reference to the same underlying storage location. This fact is visible
when new values are assigned to the variable. Obviously, if two closures capture
*different* variables, there is no sharing.
-->
闭包捕获变量。当两个闭包捕获同一变量时，它们共享对同一底层存储位置的引用。给变量赋新值时，这一事实就看得见。显然，若两个闭包捕获的是*不同*变量，就没有共享。

```lox
var globalOne;
var globalTwo;

fun main() {
  {
    var a = "one";
    fun one() {
      print a;
    }
    globalOne = one;
  }

  {
    var a = "two";
    fun two() {
      print a;
    }
    globalTwo = two;
  }
}

main();
globalOne();
globalTwo();
```

<!--
This prints "one" then "two". In this example, it's pretty clear that the two
`a` variables are different. But it's not always so obvious. Consider:
-->
这会打印 `"one"` 然后 `"two"`。在这个例子里，两个 `a` 变量显然不同。但并不总是这么显而易见。想想：

```lox
var globalOne;
var globalTwo;

fun main() {
  for (var a = 1; a <= 2; a = a + 1) {
    fun closure() {
      print a;
    }
    if (globalOne == nil) {
      globalOne = closure;
    } else {
      globalTwo = closure;
    }
  }
}

main();
globalOne();
globalTwo();
```

<!--
The code is convoluted because Lox has no collection types. The important part
is that the `main()` function does two iterations of a `for` loop. Each time
through the loop, it creates a closure that captures the loop variable. It
stores the first closure in `globalOne` and the second in `globalTwo`.
-->
代码绕得很，因为 Lox 没有集合类型。要紧的是：`main()` 对一个 `for` 循环做两次迭代。每次穿过循环，它创建一个捕获循环变量的闭包。第一个闭包存进 `globalOne`，第二个存进 `globalTwo`。

<!--
There are definitely two different closures. Do they close over two different
variables? Is there only one `a` for the entire duration of the loop, or does
each iteration get its own distinct `a` variable?
-->
闭包肯定是两个不同的。它们关闭的是两个不同变量吗？整个循环期间只有一个 `a`，还是每次迭代各有自己的、不同的 `a` 变量？

<!--
The script here is strange and contrived, but this does show up in real code
in languages that aren't as minimal as clox. Here's a JavaScript example:
-->
这儿的脚本古怪而刻意，但在不像 clox 那么极简的语言里，这确实会出现在真实代码中。这儿是一个 JavaScript 例子：

```js
var closures = [];
for (var i = 1; i <= 2; i++) {
  closures.push(function () { console.log(i); });
}

closures[0]();
closures[1]();
```

<!--
Does this print "1" then "2", or does it print <span name="three">"3"</span>
twice? You may be surprised to hear that it prints "3" twice. In this JavaScript
program, there is only a single `i` variable whose lifetime includes all
iterations of the loop, including the final exit.
-->
这会打印 `"1"` 然后 `"2"`，还是打印两次 <span name="three">`"3"`</span>？你或许会惊讶：它打印两次 `"3"`。在这个 JavaScript 程序里，只有一个 `i` 变量，其寿命涵盖循环的全部迭代，包括最后退出。

<aside name="three">

<!--
You're wondering how *three* enters the picture? After the second iteration,
`i++` is executed, which increments `i` to three. That's what causes `i <= 2` to
evaluate to false and end the loop. If `i` never reached three, the loop would
run forever.
-->
你在想*三*是怎么冒出来的？第二次迭代之后会执行 `i++`，把 `i` 加到三。正是这让 `i <= 2` 为假并结束循环。若 `i` 永远到不了三，循环就会永远跑下去。

</aside>

<!--
If you're familiar with JavaScript, you probably know that variables declared
using `var` are implicitly *hoisted* to the surrounding function or top-level
scope. It's as if you really wrote this:
-->
若你熟悉 JavaScript，大概知道用 `var` 声明的变量会隐式*提升*到外围函数或顶层作用域。就好像你其实写的是：

```js
var closures = [];
var i;
for (i = 1; i <= 2; i++) {
  closures.push(function () { console.log(i); });
}

closures[0]();
closures[1]();
```

<!--
At that point, it's clearer that there is only a single `i`. Now consider if
you change the program to use the newer `let` keyword:
-->
到这一步，更清楚只有一个 `i` 了。现在想想，若把程序改成用较新的 `let` 关键字：

```js
var closures = [];
for (let i = 1; i <= 2; i++) {
  closures.push(function () { console.log(i); });
}

closures[0]();
closures[1]();
```

<!--
Does this new program behave the same? Nope. In this case, it prints "1" then
"2". Each closure gets its own `i`. That's sort of strange when you think about
it. The increment clause is `i++`. That looks very much like it is assigning to
and mutating an existing variable, not creating a new one.
-->
这个新程序行为一样吗？不。这种情况下，它打印 `"1"` 然后 `"2"`。每个闭包各有自己的 `i`。细想有点怪。递增子句是 `i++`。看起来非常像在给已有变量赋值并修改它，而不是创建新的。

<!--
Let's try some other languages. Here's Python:
-->
再试试别的语言。这儿是 Python：

```python
closures = []
for i in range(1, 3):
  closures.append(lambda: print(i))

closures[0]()
closures[1]()
```

<!--
Python doesn't really have block scope. Variables are implicitly declared and
are automatically scoped to the surrounding function. Kind of like hoisting in
JS, now that I think about it. So both closures capture the same variable.
Unlike C, though, we don't exit the loop by incrementing `i` *past* the last
value, so this prints "2" twice.
-->
Python 其实没有块作用域。变量是隐式声明的，并自动作用于外围函数。现在想想，有点像 JS 里的提升。所以两个闭包捕获同一个变量。不过和 C 不同，我们不是靠把 `i` 递增到*越过*最后一个值来退出循环，所以这打印两次 `"2"`。

<!--
What about Ruby? Ruby has two typical ways to iterate numerically. Here's the
classic imperative style:
-->
那 Ruby 呢？Ruby 有两种典型的数值迭代方式。这儿是经典的命令式风格：

```ruby
closures = []
for i in 1..2 do
  closures << lambda { puts i }
end

closures[0].call
closures[1].call
```

<!--
This, like Python, prints "2" twice. But the more idiomatic Ruby style is using
a higher-order `each()` method on range objects:
-->
这和 Python 一样，打印两次 `"2"`。但更地道的 Ruby 风格是在 range 对象上用高阶的 `each()` 方法：

```ruby
closures = []
(1..2).each do |i|
  closures << lambda { puts i }
end

closures[0].call
closures[1].call
```

<!--
If you're not familiar with Ruby, the `do |i| ... end` part is basically a
closure that gets created and passed to the `each()` method. The `|i|` is the
parameter signature for the closure. The `each()` method invokes that closure
twice, passing in 1 for `i` the first time and 2 the second time.
-->
若不熟悉 Ruby，`do |i| ... end` 部分基本上就是一个创建后传给 `each()` 的闭包。`|i|` 是闭包的参数签名。`each()` 调用该闭包两次，第一次给 `i` 传入 1，第二次传入 2。

<!--
In this case, the "loop variable" is really a function parameter. And, since
each iteration of the loop is a separate invocation of the function, those are
definitely separate variables for each call. So this prints "1" then "2".
-->
这种情况下，“循环变量”其实是函数参数。而且，既然每次循环迭代都是对该函数的一次单独调用，那对每次调用来说肯定是不同的变量。所以这打印 `"1"` 然后 `"2"`。

<!--
If a language has a higher-level iterator-based looping structure like `foreach`
in C#, Java's "enhanced for", `for-of` in JavaScript, `for-in` in Dart, etc.,
then I think it's natural to the reader to have each iteration create a new
variable. The code *looks* like a new variable because the loop header looks
like a variable declaration. And there's no increment expression that looks like
it's mutating that variable to advance to the next step.
-->
若一门语言有更高级的、基于迭代器的循环结构——如 C# 的 `foreach`、Java 的“增强 for”、JavaScript 的 `for-of`、Dart 的 `for-in` 等——那么我认为，让每次迭代创建新变量，对读者来说很自然。代码*看起来*像新变量，因为循环头看起来像变量声明。也没有看起来像在修改该变量以推进下一步的递增表达式。

<!--
If you dig around StackOverflow and other places, you find evidence that this is
what users expect, because they are very surprised when they *don't* get it. In
particular, C# originally did *not* create a new loop variable for each
iteration of a `foreach` loop. This was such a frequent source of user confusion
that they took the very rare step of shipping a breaking change to the language.
In C# 5, each iteration creates a fresh variable.
-->
若你在 StackOverflow 和其他地方翻翻，会找到证据表明这正是用户所期望的——因为得不到时他们会非常惊讶。尤其是，C# 起初对 `foreach` 循环的每次迭代*并不*创建新的循环变量。这成了用户困惑的频繁来源，以致他们采取了极少见的一步：给语言发布破坏性变更。在 C# 5 里，每次迭代创建崭新的变量。

<!--
Old C-style `for` loops are harder. The increment clause really does look like
mutation. That implies there is a single variable that's getting updated each
step. But it's almost never *useful* for each iteration to share a loop
variable. The only time you can even detect this is when closures capture it.
And it's rarely helpful to have a closure that references a variable whose value
is whatever value caused you to exit the loop.
-->
老式的 C 风格 `for` 循环更棘手。递增子句看起来确实像修改。那暗示存在一个每一步都被更新的单一变量。但让每次迭代共享循环变量几乎从不*有用*。你甚至能察觉这一点，通常只在闭包捕获它的时候。而且，让闭包引用一个其值正是导致你退出循环的那个值的变量，也很少有帮助。

<!--
The pragmatically useful answer is probably to do what JavaScript does with
`let` in `for` loops. Make it look like mutation but actually create a new
variable each time, because that's what users want. It is kind of weird when you
think about it, though.
-->
从实用角度，有用的答案大概是学 JavaScript 在 `for` 循环里对 `let` 的做法：看起来像修改，实际上每次创建新变量，因为那是用户想要的。不过细想起来，也挺怪的。

</div>
