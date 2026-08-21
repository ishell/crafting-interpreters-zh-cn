# 局部变量

<!--
> And as imagination bodies forth<br />
> The forms of things unknown, the poet's pen<br />
> Turns them to shapes and gives to airy nothing<br />
> A local habitation and a name.
>
> <cite>William Shakespeare, <em>A Midsummer Night's Dream</em></cite>
-->
> 当想象力把那些无名之物<br />
> 一一赋形，诗人的笔<br />
> 便替它们描出轮廓，让一片空虚的乌有<br />
> 有了栖身的居所，也有了名字。
>
> <cite>威廉·莎士比亚，<em>《仲夏夜之梦》</em></cite>

<!--
The [last chapter][] introduced variables to clox, but only of the <span
name="global">global</span> variety. In this chapter, we'll extend that to
support blocks, block scope, and local variables. In jlox, we managed to pack
all of that and globals into one chapter. For clox, that's two chapters worth of
work partially because, frankly, everything takes more effort in C.
-->
[上一章][last chapter]为 clox 引入了变量，但只有<span name="global">全局</span>这一种。本章我们要把它拓展开去，让它支持块、块作用域和局部变量。在 jlox 里，我们好歹把这些连同全局变量一起塞进了一章；到了 clox，同样的内容却值两章的工分——部分原因在于，说实话，任何事情放到 C 里都要多费一番力气。

<aside name="global">

<!--
There's probably some dumb "think globally, act locally" joke here, but I'm
struggling to find it.
-->
这里大概能凑出一个“胸怀全局，落手局部”之类的蹩脚笑话，可我怎么也想不出该怎么讲。

</aside>

[last chapter]: global-variables.html

<!--
But an even more important reason is that our approach to local variables will
be quite different from how we implemented globals. Global variables are late
bound in Lox. "Late" in this context means "resolved after compile time". That's
good for keeping the compiler simple, but not great for performance. Local
variables are one of the most-used <span name="params">parts</span> of a
language. If locals are slow, *everything* is slow. So we want a strategy for
local variables that's as efficient as possible.
-->
但更要紧的理由是：我们处理局部变量的路子，将与实现全局变量时大不相同。Lox 里的全局变量是晚绑定的——此处的“晚”意思是“在编译期之后才解析”。这有利于让编译器保持简单，对性能却不太友好。而局部变量是一门语言中使用最频繁的<span name="params">部件</span>之一。局部变量一慢，*一切*都慢。所以我们想为局部变量找一套尽可能高效的策略。

<aside name="params">

<!--
Function parameters are also heavily used. They work like local variables too,
so we'll use the same implementation technique for them.
-->
函数参数同样用得极多。它们的行为也和局部变量一样，因此我们会对它们采用同一套实现技巧。

</aside>

<!--
Fortunately, lexical scoping is here to help us. As the name implies, lexical
scope means we can resolve a local variable just by looking at the text of the
program -- locals are *not* late bound. Any processing work we do in the
compiler is work we *don't* have to do at runtime, so our implementation of
local variables will lean heavily on the compiler.
-->
所幸，词法作用域正是来帮我们的。顾名思义，词法作用域意味着我们只要看程序的文本就能解析出一个局部变量——局部变量*不是*晚绑定的。凡是在编译器里做掉的处理，运行时就*不必*再做一遍；因此，我们对局部变量的实现将极大地倚重编译器。

<!--
-- Representing Local Variables
-->
## 表示局部变量

<!--
The nice thing about hacking on a programming language in modern times is
there's a long lineage of other languages to learn from. So how do C and Java
manage their local variables? Why, on the stack, of course! They typically use
the native stack mechanisms supported by the chip and OS. That's a little too
low level for us, but inside the virtual world of clox, we have our own stack we
can use.
-->
在当今这个时代捣鼓编程语言，有一桩美事：身后有一长串前辈语言可供借鉴。那么，C 和 Java 是怎么管理局部变量的？当然是放在栈上啊！它们一般直接使用芯片与操作系统提供的原生栈机制。这对我们来说层次太低了，不过在 clox 的虚拟世界里，我们自有一个可用的栈。

<!--
Right now, we only use it for holding on to **temporaries** -- short-lived blobs
of data that we need to remember while computing an expression. As long as we
don't get in the way of those, we can stuff our local variables onto the stack
too. This is great for performance. Allocating space for a new local requires
only incrementing the `stackTop` pointer, and freeing is likewise a decrement.
Accessing a variable from a known stack slot is an indexed array lookup.
-->
眼下我们只用它来存放**临时值**——那些计算表达式时需要临时记住的短命数据块。只要不碍着它们的事，我们也可以把局部变量塞到栈上。这对性能大有好处：为一个新的局部变量分配空间，只需把 `stackTop` 指针加一；释放同理，减一即可。而从一个已知的栈槽里访问变量，就是一次带下标的数组查找。

<!--
We do need to be careful, though. The VM expects the stack to behave like, well,
a stack. We have to be OK with allocating new locals only on the top of the
stack, and we have to accept that we can discard a local only when nothing is
above it on the stack. Also, we need to make sure temporaries don't interfere.
-->
不过我们确实得小心。虚拟机指望这个栈的行为像——嗯——一个栈。我们必须接受只能在栈顶分配新的局部变量，也必须接受只有当某个局部变量之上再无他物时才能丢弃它。另外，还得确保临时值不来搅局。

<!--
Conveniently, the design of Lox is in <span name="harmony">harmony</span> with
these constraints. New locals are always created by declaration statements.
Statements don't nest inside expressions, so there are never any temporaries on
the stack when a statement begins executing. Blocks are strictly nested. When a
block ends, it always takes the innermost, most recently declared locals with
it. Since those are also the locals that came into scope last, they should be on
top of the stack where we need them.
-->
巧的是，Lox 的设计与这些约束十分<span name="harmony">合拍</span>。新的局部变量总是由声明语句创造出来。语句不会嵌在表达式里，所以一条语句开始执行时，栈上绝不会有任何临时值。块是严格嵌套的。一个块结束时，它带走的总是最内层、最近声明的那些局部变量。而这些局部变量也正是最后进入作用域的，因此它们理应待在栈顶——正是我们需要它们在的地方。

<aside name="harmony">

<!--
This alignment obviously isn't coincidental. I designed Lox to be amenable to
single-pass compilation to stack-based bytecode. But I didn't have to tweak the
language too much to fit in those restrictions. Most of its design should feel
pretty natural.

This is in large part because the history of languages is deeply tied to
single-pass compilation and -- to a lesser degree -- stack-based architectures.
Lox's block scoping follows a tradition stretching back to BCPL. As programmers,
our intuition of what's "normal" in a language is informed even today by the
hardware limitations of yesteryear.
-->
这种契合当然不是碰巧。我设计 Lox 时，就有意让它便于单遍编译成基于栈的字节码。但为了迁就这些限制，我并不需要对语言做太多改动——它的大部分设计读起来都相当自然。

这在很大程度上是因为，语言的历史与单遍编译、以及（程度稍轻的）基于栈的体系结构，纠缠得极深。Lox 的块作用域承袭的是一路上溯至 BCPL 的传统。作为程序员，我们对一门语言里什么算“寻常”的直觉，时至今日仍受着昔年硬件局限的塑造。

</aside>

<!--
Step through this example program and watch how the local variables come in and
go out of scope:
-->
一步步走过下面这个示例程序，看看局部变量是如何进入和退出作用域的：

<img src="image/local-variables/scopes.png" alt="A series of local variables come into and out of scope in a stack-like fashion." />

<!--
See how they fit a stack perfectly? It seems that the stack will work for
storing locals at runtime. But we can go further than that. Not only do we know
*that* they will be on the stack, but we can even pin down precisely *where*
they will be on the stack. Since the compiler knows exactly which local
variables are in scope at any point in time, it can effectively simulate the
stack during compilation and note <span name="fn">where</span> in the stack each
variable lives.
-->
看到它们和栈契合得多么完美了吗？看来在运行时用栈来存放局部变量是行得通的。但我们还能再走远一步。我们不只知道它们*会*在栈上，甚至能精确地钉死它们*在栈的哪个位置*。既然编译器在任一时刻都确切知道哪些局部变量处于作用域中，它便可以在编译期有效地模拟这个栈，并记下每个变量住在栈里的<span name="fn">哪一格</span>。

<!--
We'll take advantage of this by using these stack offsets as operands for the
bytecode instructions that read and store local variables. This makes working
with locals deliciously fast -- as simple as indexing into an array.
-->
我们要利用这一点：把这些栈偏移量当作读写局部变量的字节码指令的操作数。如此一来，操作局部变量就快得令人愉悦——简单得如同给数组下个标。

<aside name="fn">

<!--
In this chapter, locals start at the bottom of the VM's stack array and are
indexed from there. When we add [functions][], that scheme gets a little more
complex. Each function needs its own region of the stack for its parameters and
local variables. But, as we'll see, that doesn't add as much complexity as you
might expect.
-->
本章里，局部变量从虚拟机栈数组的底部开始，并由此编号。等我们加入[函数][functions]，这套方案会稍稍复杂一些：每个函数都需要栈上属于自己的一块区域，来放它的参数和局部变量。不过我们将会看到，这带来的复杂度并不像你想象的那么多。

[functions]: calls-and-functions.html

</aside>

<!--
There's a lot of state we need to track in the compiler to make this whole thing
go, so let's get started there. In jlox, we used a linked chain of "environment"
HashMaps to track which local variables were currently in scope. That's sort of
the classic, schoolbook way of representing lexical scope. For clox, as usual,
we're going a little closer to the metal. All of the state lives in a new
struct.
-->
要把这整套东西跑起来，编译器里有不少状态需要追踪，我们就从那儿动手。在 jlox 中，我们用一条“环境” HashMap 的链来追踪当前哪些局部变量处于作用域内——那算是表示词法作用域的经典教科书做法。而对 clox，一如往常，我们要更贴近机器一些。所有状态都住在一个新的结构体里。

^code compiler-struct (1 before, 2 after)

<!--
We have a simple, flat array of all locals that are in scope during each point in
the compilation process. They are <span name="order">ordered</span> in the array
in the order that their declarations appear in the code. Since the instruction
operand we'll use to encode a local is a single byte, our VM has a hard limit on
the number of locals that can be in scope at once. That means we can also give
the locals array a fixed size.
-->
我们有一个简单、扁平的数组，装着编译过程中每一时刻处于作用域内的所有局部变量。它们在数组中的<span name="order">次序</span>，就是其声明在代码里出现的次序。由于我们用来编码局部变量的指令操作数只有一个字节，虚拟机对同时处于作用域内的局部变量数目就有了一个硬性上限。这也意味着我们可以给这个局部变量数组一个固定大小。

<aside name="order">

<!--
We're writing a single-pass compiler, so it's not like we have *too* many other
options for how to order them in the array.
-->
我们写的是单遍编译器，所以在数组里怎么排序这件事上，可选的余地本也*没多少*。

</aside>

^code uint8-count (1 before, 2 after)

<!--
Back in the Compiler struct, the `localCount` field tracks how many locals are
in scope -- how many of those array slots are in use. We also track the "scope
depth". This is the number of blocks surrounding the current bit of code we're
compiling.
-->
回到 Compiler 结构体，`localCount` 字段追踪有多少局部变量处于作用域内——也就是数组里有多少槽位正被占用。我们还追踪“作用域深度”，即包围着当前正在编译的这段代码的块的层数。

<!--
Our Java interpreter used a chain of maps to keep each block's variables
separate from other blocks'. This time, we'll simply number variables with the
level of nesting where they appear. Zero is the global scope, one is the first
top-level block, two is inside that, you get the idea. We use this to track
which block each local belongs to so that we know which locals to discard when a
block ends.
-->
我们的 Java 解释器用一条 map 链，把各个块的变量彼此隔开。这一回，我们干脆用变量出现处的嵌套层级给它们编号：零是全局作用域，一是最外层的第一个块，二在其内部，以此类推。我们靠它来追踪每个局部变量归属哪个块，这样块结束时就知道该丢弃哪些局部变量。

<!--
Each local in the array is one of these:
-->
数组里的每个局部变量都是这么个东西：

^code local-struct (1 before, 2 after)

<!--
We store the name of the variable. When we're resolving an identifier, we
compare the identifier's lexeme with each local's name to find a match. It's
pretty hard to resolve a variable if you don't know its name. The `depth` field
records the scope depth of the block where the local variable was declared.
That's all the state we need for now.
-->
我们存下变量的名字。解析标识符时，我们把标识符的词素与每个局部变量的名字比对，以找出匹配。毕竟，不知道变量的名字，是很难解析它的。`depth` 字段记录声明该局部变量的那个块的作用域深度。眼下我们需要的状态就这些。

<!--
This is a very different representation from what we had in jlox, but it still
lets us answer all of the same questions our compiler needs to ask of the
lexical environment. The next step is figuring out how the compiler *gets* at
this state. If we were <span name="thread">principled</span> engineers, we'd
give each function in the front end a parameter that accepts a pointer to a
Compiler. We'd create a Compiler at the beginning and carefully thread it
through each function call... but that would mean a lot of boring changes to
the code we already wrote, so here's a global variable instead:
-->
这与我们在 jlox 里的表示大相径庭，但它依然能回答编译器需要向词法环境提出的所有那些问题。下一步是想清楚编译器怎样*拿到*这些状态。倘若我们是<span name="thread">讲原则</span>的工程师，就该给前端的每个函数都加一个接收 Compiler 指针的参数，一开始创建一个 Compiler，再小心翼翼地把它穿过每一次函数调用……可那意味着要对已经写好的代码做一大堆无聊的改动，所以，还是来个全局变量吧：

<aside name="thread">

<!--
In particular, if we ever want to use our compiler in a multi-threaded
application, possibly with multiple compilers running in parallel, then using a
global variable is a *bad* idea.
-->
特别是，假如我们哪天想在多线程应用里使用这个编译器，甚至让多个编译器并行运转，那么用全局变量就是个*糟糕*的主意。

</aside>

^code current-compiler (1 before, 1 after)

<!--
Here's a little function to initialize the compiler:
-->
这里有个小函数用来初始化编译器：

^code init-compiler

<!--
When we first start up the VM, we call it to get everything into a clean state.
-->
虚拟机刚启动时，我们调用它，把一切都置入干净的状态。

^code compiler (1 before, 1 after)

<!--
Our compiler has the data it needs, but not the operations on that data. There's
no way to create and destroy scopes, or add and resolve variables. We'll add
those as we need them. First, let's start building some language features.
-->
编译器有了它需要的数据，却还没有作用于这些数据的操作：没法创建和销毁作用域，也没法添加和解析变量。我们会在需要时逐一补上。先来动手造几个语言特性。

<!--
-- Block Statements
-->
## 块语句

<!--
Before we can have any local variables, we need some local scopes. These come
from two things: function bodies and <span name="block">blocks</span>. Functions
are a big chunk of work that we'll tackle in [a later chapter][functions], so
for now we're only going to do blocks. As usual, we start with the syntax. The
new grammar we'll introduce is:
-->
要有局部变量，先得有局部作用域。局部作用域来自两处：函数体和<span name="block">块</span>。函数是一大摊活儿，我们留到[后面的章节][functions]再收拾，眼下只做块。照例，我们从语法开始。要引入的新文法是：

```ebnf
statement      → exprStmt
               | printStmt
               | block ;

block          → "{" declaration* "}" ;
```

<aside name="block">

<!--
When you think about it, "block" is a weird name. Used metaphorically, "block"
usually means a small indivisible unit, but for some reason, the Algol 60
committee decided to use it to refer to a *compound* structure -- a series of
statements. It could be worse, I suppose. Algol 58 called `begin` and `end`
"statement parentheses".
-->
细想一下，“块”（block）这名字挺怪的。作比喻用时，“block”通常指一个小而不可分的单元；可不知怎的，Algol 60 委员会偏偏决定拿它指代一种*复合*结构——一串语句。我猜情况本可以更糟：Algol 58 管 `begin` 和 `end` 叫“语句括号”。

<img src="image/local-variables/block.png" alt="A cinder block." class="above" />

</aside>

<!--
Blocks are a kind of statement, so the rule for them goes in the `statement`
production. The corresponding code to compile one looks like this:
-->
块是语句的一种，所以它的规则放进 `statement` 产生式。编译一个块的相应代码长这样：

^code parse-block (2 before, 1 after)

<!--
After <span name="helper">parsing</span> the initial curly brace, we use this
helper function to compile the rest of the block:
-->
<span name="helper">解析</span>掉起始的花括号之后，我们用这个辅助函数来编译块的余下部分：

<aside name="helper">

<!--
This function will come in handy later for compiling function bodies.
-->
稍后编译函数体时，这个函数会派上用场。

</aside>

^code block

<!--
It keeps parsing declarations and statements until it hits the closing brace. As
we do with any loop in the parser, we also check for the end of the token
stream. This way, if there's a malformed program with a missing closing curly,
the compiler doesn't get stuck in a loop.
-->
它不断解析声明和语句，直到撞上收尾的花括号。和解析器里任何循环一样，我们也要检查记号流是否已到尽头。这样，若程序畸形、少了个收尾花括号，编译器也不会陷在循环里出不来。

<!--
Executing a block simply means executing the statements it contains, one after
the other, so there isn't much to compiling them. The semantically interesting
thing blocks do is create scopes. Before we compile the body of a block, we call
this function to enter a new local scope:
-->
执行一个块，无非是把它包含的语句一条接一条执行下去，所以编译起来没多少花样。块在语义上真正有趣的事是创建作用域。在编译块体之前，我们调用这个函数进入一个新的局部作用域：

^code begin-scope

<!--
In order to "create" a scope, all we do is increment the current depth. This is
certainly much faster than jlox, which allocated an entire new HashMap for
each one. Given `beginScope()`, you can probably guess what `endScope()` does.
-->
为了“创建”一个作用域，我们做的仅仅是把当前深度加一。这显然比 jlox 快得多——那边每个作用域都要分配一整张新 HashMap。有了 `beginScope()`，你大概能猜到 `endScope()` 干什么。

^code end-scope

<!--
That's it for blocks and scopes -- more or less -- so we're ready to stuff some
variables into them.
-->
块和作用域大抵就这些了，于是我们可以往里头塞点变量了。

<!--
-- Declaring Local Variables
-->
## 声明局部变量

<!--
Usually we start with parsing here, but our compiler already supports parsing
and compiling variable declarations. We've got `var` statements, identifier
expressions and assignment in there now. It's just that the compiler assumes
all variables are global. So we don't need any new parsing support, we just need
to hook up the new scoping semantics to the existing code.
-->
通常这里我们会从解析开始，但我们的编译器已经支持解析和编译变量声明了：`var` 语句、标识符表达式和赋值都已在其中，只是编译器假定所有变量都是全局的。所以我们不需要任何新的解析支持，只需把新的作用域语义接到既有代码上。

<img src="image/local-variables/declaration.png" alt="The code flow within varDeclaration()." />

<!--
Variable declaration parsing begins in `varDeclaration()` and relies on a couple
of other functions. First, `parseVariable()` consumes the identifier token for
the variable name, adds its lexeme to the chunk's constant table as a string,
and then returns the constant table index where it was added. Then, after
`varDeclaration()` compiles the initializer, it calls `defineVariable()` to emit
the bytecode for storing the variable's value in the global variable hash table.
-->
变量声明的解析始于 `varDeclaration()`，并依赖另外几个函数。首先，`parseVariable()` 消耗变量名的标识符记号，把它的词素作为字符串加入 chunk 的常量表，然后返回它被加入的常量表下标。接着，`varDeclaration()` 编译完初始化式后，调用 `defineVariable()` 发出字节码，把变量的值存进全局变量哈希表。

<!--
Both of those helpers need a few changes to support local variables. In
`parseVariable()`, we add:
-->
这两个辅助函数都需要改动几处，才能支持局部变量。在 `parseVariable()` 中，我们加上：

^code parse-local (1 before, 1 after)

<!--
First, we "declare" the variable. I'll get to what that means in a second. After
that, we exit the function if we're in a local scope. At runtime, locals aren't
looked up by name. There's no need to stuff the variable's name into the
constant table, so if the declaration is inside a local scope, we return a dummy
table index instead.
-->
首先，我们“声明”这个变量——这是什么意思，我马上就说。之后，若身处局部作用域，就直接退出函数。运行时并不按名字查找局部变量，也就没必要把变量名塞进常量表；所以若声明位于局部作用域内，我们改为返回一个占位的表下标。

<!--
Over in `defineVariable()`, we need to emit the code to store a local variable
if we're in a local scope. It looks like this:
-->
到了 `defineVariable()` 这边，若身处局部作用域，我们需要发出存储局部变量的代码。它长这样：

^code define-variable (1 before, 1 after)

<!--
Wait, what? Yup. That's it. There is no code to create a local variable at
runtime. Think about what state the VM is in. It has already executed the code
for the variable's initializer (or the implicit `nil` if the user omitted an
initializer), and that value is sitting right on top of the stack as the only
remaining temporary. We also know that new locals are allocated at the top of
the stack... right where that value already is. Thus, there's nothing to do. The
temporary simply *becomes* the local variable. It doesn't get much more
efficient than that.
-->
等等，什么？没错，就这样。运行时并没有创建局部变量的代码。想想虚拟机此刻的状态：它已经执行了变量初始化式的代码（若用户省略了初始化式，则是那个隐含的 `nil`），而那个值正稳稳坐在栈顶，是仅剩的一个临时值。我们还知道，新的局部变量分配在栈顶……恰恰就是那个值已经在的位置。于是，什么也不用做。那个临时值径直*变成*了局部变量。再高效也不过如此了。

<span name="locals"></span>

<img src="image/local-variables/local-slots.png" alt="Walking through the bytecode execution showing that each initializer's result ends up in the local's slot." />

<aside name="locals">

<!--
The code on the left compiles to the sequence of instructions on the right.
-->
左边的代码编译成右边的指令序列。

</aside>

<!--
OK, so what's "declaring" about? Here's what that does:
-->
好，那么“声明”又是怎么回事？它做的是这些：

^code declare-variable

<!--
This is the point where the compiler records the existence of the variable. We
only do this for locals, so if we're in the top-level global scope, we just bail
out. Because global variables are late bound, the compiler doesn't keep track of
which declarations for them it has seen.
-->
这里正是编译器记下变量存在的地方。我们只对局部变量这么做，所以若身处顶层的全局作用域，就干脆抽身而去。因为全局变量是晚绑定的，编译器并不追踪自己见过哪些针对它们的声明。

<!--
But for local variables, the compiler does need to remember that the variable
exists. That's what declaring it does -- it adds it to the compiler's list of
variables in the current scope. We implement that using another new function.
-->
但对局部变量，编译器确实需要记住这个变量存在。这就是声明它的作用——把它加入编译器中当前作用域的变量列表。我们用另一个新函数来实现。

^code add-local

<!--
This initializes the next available Local in the compiler's array of variables.
It stores the variable's <span name="lexeme">name</span> and the depth of the
scope that owns the variable.
-->
它在编译器的变量数组里初始化下一个可用的 Local，存下变量的<span name="lexeme">名字</span>，以及拥有该变量的那个作用域的深度。

<aside name="lexeme">

<!--
Worried about the lifetime of the string for the variable's name? The Local
directly stores a copy of the Token struct for the identifier. Tokens store a
pointer to the first character of their lexeme and the lexeme's length. That
pointer points into the original source string for the script or REPL entry
being compiled.

As long as that string stays around during the entire compilation process --
which it must since, you know, we're compiling it -- then all of the tokens
pointing into it are fine.
-->
在担心变量名那个字符串的生命期？Local 直接存了标识符的 Token 结构体的一份副本。Token 里存的是指向其词素首字符的指针和词素长度，而这个指针指向正在被编译的脚本或 REPL 输入的原始源字符串。

只要那个字符串在整个编译过程中一直健在——它必须健在，因为，你知道的，我们正在编译它——那么所有指向它的记号就都安然无恙。

</aside>

<!--
Our implementation is fine for a correct Lox program, but what about invalid
code? Let's aim to be robust. The first error to handle is not really the user's
fault, but more a limitation of the VM. The instructions to work with local
variables refer to them by slot index. That index is stored in a single-byte
operand, which means the VM only supports up to 256 local variables in scope at
one time.
-->
对一个正确的 Lox 程序，我们的实现没问题；可无效代码怎么办？我们求的是稳健。第一个要处理的错误其实不算用户的过失，更像是虚拟机的局限：操作局部变量的指令按槽位下标引用它们，而这个下标存在一个单字节操作数里，也就是说虚拟机最多只支持同时有 256 个局部变量处于作用域内。

<!--
If we try to go over that, not only could we not refer to them at runtime, but
the compiler would overwrite its own locals array, too. Let's prevent that.
-->
若试图越过这个数目，不仅运行时无法引用它们，编译器还会把自己的局部变量数组给覆盖掉。我们来防住它。

^code too-many-locals (1 before, 1 after)

<!--
The next case is trickier. Consider:
-->
下一种情形更微妙。请看：

```lox
{
  var a = "first";
  var a = "second";
}
```

<!--
At the top level, Lox allows redeclaring a variable with the same name as a
previous declaration because that's useful for the REPL. But inside a local
scope, that's a pretty <span name="rust">weird</span> thing to do. It's likely
to be a mistake, and many languages, including our own Lox, enshrine that
assumption by making this an error.
-->
在顶层，Lox 允许用与先前声明同名的方式重新声明变量，因为这对 REPL 很有用。但在局部作用域内，这么干就相当<span name="rust">古怪</span>了。它很可能是个笔误；许多语言，包括我们自己的 Lox，都把这一假设奉为准则，将其定为错误。

<aside name="rust">

<!--
Interestingly, the Rust programming language *does* allow this, and idiomatic
code relies on it.
-->
有趣的是，Rust 语言*确实*允许这么做，而且地道的 Rust 代码正倚仗于此。

</aside>

<!--
Note that the above program is different from this one:
-->
注意，上面那个程序与下面这个不同：

```lox
{
  var a = "outer";
  {
    var a = "inner";
  }
}
```

<!--
It's OK to have two variables with the same name in *different* scopes, even
when the scopes overlap such that both are visible at the same time. That's
shadowing, and Lox does allow that. It's only an error to have two variables
with the same name in the *same* local scope.
-->
在*不同*作用域里有两个同名变量是可以的，哪怕作用域相互重叠、两者同时可见也无妨。那叫遮蔽（shadowing），Lox 是允许的。只有在*同一个*局部作用域里有两个同名变量才算错误。

<!--
We detect that error like so:
-->
我们这样检出该错误：

^code existing-in-scope (1 before, 2 after)

<aside name="negative">

<!--
Don't worry about that odd `depth != -1` part yet. We'll get to what that's
about later.
-->
暂且别管那个古怪的 `depth != -1`。它是怎么回事，我们稍后再说。

</aside>

<!--
Local variables are appended to the array when they're declared, which means the
current scope is always at the end of the array. When we declare a new variable,
we start at the end and work backward, looking for an existing variable with the
same name. If we find one in the current scope, we report the error. Otherwise,
if we reach the beginning of the array or a variable owned by another scope,
then we know we've checked all of the existing variables in the scope.
-->
局部变量在声明时被追加到数组末尾，也就是说当前作用域总是位于数组的尾部。声明新变量时，我们从末尾出发向前回溯，寻找已存在的同名变量。若在当前作用域里找到了，就报告错误；反之，若走到了数组开头，或碰上归属另一个作用域的变量，就知道该作用域里已有的变量都查遍了。

<!--
To see if two identifiers are the same, we use this:
-->
判断两个标识符是否相同，我们用这个：

^code identifiers-equal

<!--
Since we know the lengths of both lexemes, we check that first. That will fail
quickly for many non-equal strings. If the <span name="hash">lengths</span> are
the same, we check the characters using `memcmp()`. To get to `memcmp()`, we
need an include.
-->
既然两个词素的长度都是已知的，就先查长度。对许多不相等的字符串，这一步会飞快地否掉。若<span name="hash">长度</span>相同，我们再用 `memcmp()` 比对字符。要用上 `memcmp()`，得加一条 include。

<aside name="hash">

<!--
It would be a nice little optimization if we could check their hashes, but
tokens aren't full LoxStrings, so we haven't calculated their hashes yet.
-->
要是能比较它们的哈希值，倒是个不错的小优化；可记号并不是完整的 LoxString，我们还没算过它们的哈希。

</aside>

^code compiler-include-string (1 before, 2 after)

<!--
With this, we're able to bring variables into being. But, like ghosts, they
linger on beyond the scope where they are declared. When a block ends, we need
to put them to rest.
-->
有了这些，我们能让变量诞生了。可它们像幽魂一样，赖在声明它们的作用域之外不肯散去。块结束时，我们得让它们安息。

^code pop-locals (1 before, 1 after)

<!--
When we pop a scope, we walk backward through the local array looking for any
variables declared at the scope depth we just left. We discard them by simply
decrementing the length of the array.
-->
弹出一个作用域时，我们向前回溯遍历局部变量数组，找出所有在刚刚离开的那个作用域深度上声明的变量。丢弃它们，只需把数组的长度减一。

<!--
There is a runtime component to this too. Local variables occupy slots on the
stack. When a local variable goes out of scope, that slot is no longer needed
and should be freed. So, for each variable that we discard, we also emit an
`OP_POP` <span name="pop">instruction</span> to pop it from the stack.
-->
这件事也有运行时的一半。局部变量占着栈上的槽位；一个局部变量离开作用域后，那个槽位便不再需要，理应释放。所以，对每个丢弃的变量，我们还会发出一条 `OP_POP` <span name="pop">指令</span>，把它从栈上弹掉。

<aside name="pop">

<!--
When multiple local variables go out of scope at once, you get a series of
`OP_POP` instructions that get interpreted one at a time. A simple optimization
you could add to your Lox implementation is a specialized `OP_POPN` instruction
that takes an operand for the number of slots to pop and pops them all at once.
-->
当多个局部变量一齐离开作用域时，你会得到一串 `OP_POP` 指令，被逐条解释执行。你可以给自己的 Lox 实现加一个简单的优化：专设一条 `OP_POPN` 指令，用一个操作数表示要弹出的槽位数，一次全部弹掉。

</aside>

<!--
-- Using Locals
-->
## 使用局部变量

<!--
We can now compile and execute local variable declarations. At runtime, their
values are sitting where they should be on the stack. Let's start using them.
We'll do both variable access and assignment at the same time since they touch
the same functions in the compiler.
-->
现在我们能编译并执行局部变量声明了；运行时，它们的值也稳坐在栈上该在的位置。该开始用起来了。我们把变量访问和赋值一并做掉，因为它们在编译器里碰的是同一批函数。

<!--
We already have code for getting and setting global variables, and -- like good
little software engineers -- we want to reuse as much of that existing code as
we can. Something like this:
-->
读写全局变量的代码我们已经有了；而作为乖巧的小软件工程师，我们想尽可能复用这些既有代码。差不多像这样：

^code named-local (1 before, 2 after)

<!--
Instead of hardcoding the bytecode instructions emitted for variable access and
assignment, we use a couple of C variables. First, we try to find a local
variable with the given name. If we find one, we use the instructions for
working with locals. Otherwise, we assume it's a global variable and use the
existing bytecode instructions for globals.
-->
我们不再把变量访问与赋值所发出的字节码指令写死，而是用两个 C 变量来存。首先，我们试着找出一个具有给定名字的局部变量；若找到了，就使用操作局部变量的指令；否则，我们假定它是全局变量，沿用既有的全局变量字节码指令。

<!--
A little further down, we use those variables to emit the right instructions.
For assignment:
-->
再往下一点，我们用这两个变量发出正确的指令。赋值：

^code emit-set (2 before, 1 after)

<!--
And for access:
-->
访问：

^code emit-get (2 before, 1 after)

<!--
The real heart of this chapter, the part where we resolve a local variable, is
here:
-->
本章真正的心脏——解析局部变量的那一段——在这里：

^code resolve-local

<!--
For all that, it's straightforward. We walk the list of locals that are
currently in scope. If one has the same name as the identifier token, the
identifier must refer to that variable. We've found it! We walk the array
backward so that we find the *last* declared variable with the identifier. That
ensures that inner local variables correctly shadow locals with the same name in
surrounding scopes.
-->
说了那么多，其实直截了当。我们遍历当前处于作用域内的局部变量列表；若某个变量与标识符记号同名，那这个标识符必定指的就是它——找到了！我们从后往前遍历数组，以便找到带该标识符的*最后*一个被声明的变量。这就保证了内层局部变量能正确遮蔽外围作用域中的同名局部变量。

<!--
At runtime, we load and store locals using the stack slot index, so that's what
the compiler needs to calculate after it resolves the variable. Whenever a
variable is declared, we append it to the locals array in Compiler. That means
the first local variable is at index zero, the next one is at index one, and so
on. In other words, the locals array in the compiler has the *exact* same layout
as the VM's stack will have at runtime. The variable's index in the locals array
is the same as its stack slot. How convenient!
-->
运行时，我们靠栈槽下标来加载和存储局部变量，因此编译器解析出变量之后需要算出的正是这个下标。每当一个变量被声明，我们就把它追加到 Compiler 的局部变量数组里。这意味着第一个局部变量在下标零，下一个在下标一，如此下去。换句话说，编译器里的局部变量数组，与运行时虚拟机栈的布局*完全*一致。变量在局部变量数组中的下标，就等于它的栈槽位。多么便利！

<!--
If we make it through the whole array without finding a variable with the given
name, it must not be a local. In that case, we return `-1` to signal that it
wasn't found and should be assumed to be a global variable instead.
-->
若把整个数组走完仍未找到给定名字的变量，它必定不是局部变量。这种情况下，我们返回 `-1`，示意没找到，应当改按全局变量来对待。

<!--
### Interpreting local variables
-->
### 解释局部变量

<!--
Our compiler is emitting two new instructions, so let's get them working. First
is loading a local variable:
-->
编译器正在发出两条新指令，我们来让它们跑起来。先是加载局部变量：

^code get-local-op (1 before, 1 after)

<!--
And its implementation:
-->
以及它的实现：

^code interpret-get-local (1 before, 1 after)

<!--
It takes a single-byte operand for the stack slot where the local lives. It
loads the value from that index and then pushes it on top of the stack where
later instructions can find it.
-->
它接受一个单字节操作数，表示该局部变量所住的栈槽位。它从那个下标处加载值，然后推到栈顶，好让后续指令能找到它。

<aside name="slot">

<!--
It seems redundant to push the local's value onto the stack since it's already
on the stack lower down somewhere. The problem is that the other bytecode
instructions only look for data at the *top* of the stack. This is the core
aspect that makes our bytecode instruction set *stack*-based.
[Register-based][reg] bytecode instruction sets avoid this stack juggling at the
cost of having larger instructions with more operands.
-->
把局部变量的值推上栈似乎显得多余，毕竟它已经在栈上更靠下的某处了。问题在于，其他字节码指令只在栈*顶*找数据。这正是让我们的字节码指令集成为*基于栈*的核心所在。[基于寄存器的][reg]字节码指令集免去了这套栈上腾挪，代价是指令更大、操作数更多。

[reg]: a-virtual-machine.html#design-note

</aside>

<!--
Next is assignment:
-->
接下来是赋值：

^code set-local-op (1 before, 1 after)

<!--
You can probably predict the implementation.
-->
实现你大概能猜到。

^code interpret-set-local (1 before, 1 after)

<!--
It takes the assigned value from the top of the stack and stores it in the stack
slot corresponding to the local variable. Note that it doesn't pop the value
from the stack. Remember, assignment is an expression, and every expression
produces a value. The value of an assignment expression is the assigned value
itself, so the VM just leaves the value on the stack.
-->
它从栈顶取出被赋的值，存进该局部变量对应的栈槽位。注意，它并不把值从栈上弹掉。记住，赋值是表达式，而每个表达式都产生一个值；赋值表达式的值就是被赋的那个值本身，所以虚拟机干脆把值留在栈上。

<!--
Our disassembler is incomplete without support for these two new instructions.
-->
少了对这两条新指令的支持，我们的反汇编器便不完整。

^code disassemble-local (1 before, 1 after)

<!--
The compiler compiles local variables to direct slot access. The local
variable's name never leaves the compiler to make it into the chunk at all.
That's great for performance, but not so great for introspection. When we
disassemble these instructions, we can't show the variable's name like we could
with globals. Instead, we just show the slot number.
-->
编译器把局部变量编译成直接的槽位访问。局部变量的名字从未离开编译器，压根没进到 chunk 里去。这对性能极好，对内省却不太妙：反汇编这些指令时，我们无法像对全局变量那样显示变量名，只能显示槽位号。

<aside name="debug">

<!--
Erasing local variable names in the compiler is a real issue if we ever want to
implement a debugger for our VM. When users step through code, they expect to
see the values of local variables organized by their names. To support that,
we'd need to output some additional information that tracks the name of each
local variable at each stack slot.
-->
若哪天我们想为虚拟机实现一个调试器，在编译器里抹掉局部变量名就是个实打实的麻烦。用户单步执行代码时，期望看到按名字组织的局部变量值。要支持这一点，我们得额外输出一些信息，追踪每个栈槽位上局部变量的名字。

</aside>

^code byte-instruction

<!--
### Another scope edge case
-->
### 又一处作用域边角

<!--
We already sunk some time into handling a couple of weird edge cases around
scopes. We made sure shadowing works correctly. We report an error if two
variables in the same local scope have the same name. For reasons that aren't
entirely clear to me, variable scoping seems to have a lot of these wrinkles.
I've never seen a language where it feels completely <span
name="elegant">elegant</span>.
-->
我们已经花了些工夫处理作用域周边几个古怪的边角情形：确保了遮蔽能正确工作；同一局部作用域里两个变量同名会报错。出于我也说不太清的原因，变量作用域似乎总有一堆这样的皱褶。我还没见过哪门语言在这件事上让人觉得彻底<span name="elegant">优雅</span>。

<aside name="elegant">

<!--
No, not even Scheme.
-->
不，连 Scheme 也不例外。

</aside>

<!--
We've got one more edge case to deal with before we end this chapter. Recall this strange beastie we first met in [jlox's implementation of variable resolution][shadow]:
-->
本章收尾之前，还有一个边角情形要料理。还记得我们在 [jlox 的变量解析实现][shadow]里初次遭遇的这头怪东西吗：

[shadow]: resolving-and-binding.html#resolving-variable-declarations

```lox
{
  var a = "outer";
  {
    var a = a;
  }
}
```

<!--
We slayed it then by splitting a variable's declaration into two phases, and
we'll do that again here:
-->
当时我们把变量的声明拆成两个阶段，将它斩于马下；这回我们照做一遍：

<img src="image/local-variables/phases.png" alt="An example variable declaration marked 'declared uninitialized' before the variable name and 'ready for use' after the initializer." />

<!--
As soon as the variable declaration begins -- in other words, before its
initializer -- the name is declared in the current scope. The variable exists,
but in a special "uninitialized" state. Then we compile the initializer. If at
any point in that expression we resolve an identifier that points back to this
variable, we'll see that it is not initialized yet and report an error. After we
finish compiling the initializer, we mark the variable as initialized and ready
for use.
-->
变量声明一开始——换言之，在它的初始化式之前——名字就已在当前作用域里被声明。变量存在了，只是处于一种特殊的“未初始化”状态。然后我们编译初始化式。若在那个表达式中的任何一点，我们解析出的标识符回指到这个变量，我们就会发现它尚未初始化，从而报告错误。初始化式编译完毕后，我们把该变量标记为已初始化、可以使用。

<!--
To implement this, when we declare a local, we need to indicate the
"uninitialized" state somehow. We could add a new field to Local, but let's be a
little more parsimonious with memory. Instead, we'll set the variable's scope
depth to a special sentinel value, `-1`.
-->
要实现这一点，声明局部变量时，我们得设法标示出“未初始化”状态。可以给 Local 加个新字段，不过我们在内存上还是抠一点吧：改为把变量的作用域深度设为一个特殊的哨兵值 `-1`。

^code declare-undefined (1 before, 1 after)

<!--
Later, once the variable's initializer has been compiled, we mark it
initialized.
-->
稍后，一旦变量的初始化式编译完成，我们就把它标记为已初始化。

^code define-local (1 before, 2 after)

<!--
That is implemented like so:
-->
其实现如下：

^code mark-initialized

<!--
So this is *really* what "declaring" and "defining" a variable means in the
compiler. "Declaring" is when the variable is added to the scope, and "defining"
is when it becomes available for use.
-->
所以，在编译器里“声明”与“定义”一个变量，*真正*的含义就在这里：“声明”是变量被加入作用域之时，“定义”是它变得可用之时。

<!--
When we resolve a reference to a local variable, we check the scope depth to see
if it's fully defined.
-->
解析对某个局部变量的引用时，我们检查作用域深度，看它是否已完全定义。

^code own-initializer-error (1 before, 1 after)

<!--
If the variable has the sentinel depth, it must be a reference to a variable in
its own initializer, and we report that as an error.
-->
若变量带着那个哨兵深度，那它必定是在自己的初始化式里引用自己，我们便将此报告为错误。

<!--
That's it for this chapter! We added blocks, local variables, and real,
honest-to-God lexical scoping. Given that we introduced an entirely different
runtime representation for variables, we didn't have to write a lot of code. The
implementation ended up being pretty clean and efficient.
-->
本章就到这里！我们加上了块、局部变量，以及真真切切、地道十足的词法作用域。考虑到我们为变量引入了一套截然不同的运行时表示，需要写的代码其实并不多，实现最终也相当干净、高效。

<!--
You'll notice that almost all of the code we wrote is in the compiler. Over in
the runtime, it's just two little instructions. You'll see this as a continuing
<span name="static">trend</span> in clox compared to jlox. One of the biggest
hammers in the optimizer's toolbox is pulling work forward into the compiler so
that you don't have to do it at runtime. In this chapter, that meant resolving
exactly which stack slot every local variable occupies. That way, at runtime, no
lookup or resolution needs to happen.
-->
你会注意到，我们写的代码几乎全在编译器里；运行时那边只有两条小小的指令。在 clox 与 jlox 的对比中，你将看到这是一个持续的<span name="static">趋势</span>。优化者工具箱里最大的锤子之一，就是把活儿提前拉到编译器里做，好让运行时不必再做。在本章，这意味着精确解析出每个局部变量占据哪个栈槽——如此一来，运行时便无需任何查找或解析。

<aside name="static">

<!--
You can look at static types as an extreme example of this trend. A statically
typed language takes all of the type analysis and type error handling and sorts
it all out during compilation. Then the runtime doesn't have to waste any time
checking that values have the proper type for their operation. In fact, in some
statically typed languages like C, you don't even *know* the type at runtime.
The compiler completely erases any representation of a value's type leaving just
the bare bits.
-->
你可以把静态类型看作这一趋势的极端例子。静态类型语言把所有类型分析与类型错误处理统统在编译期料理干净，运行时便不必浪费任何时间去检查值的类型是否配得上它所参与的运算。事实上，在 C 这样的某些静态类型语言里，运行时你甚至*无从知晓*类型：编译器把值类型的一切表示彻底抹去，只剩下赤裸的比特。

</aside>

<div class="challenges">

<!--
## Challenges
-->
## 挑战

<!--
1.  Our simple local array makes it easy to calculate the stack slot of each
    local variable. But it means that when the compiler resolves a reference to
    a variable, we have to do a linear scan through the array.

    Come up with something more efficient. Do you think the additional
    complexity is worth it?
-->
1.  我们那个简单的局部变量数组，让计算每个局部变量的栈槽位变得轻而易举。但它也意味着编译器解析对某个变量的引用时，必须对数组做一次线性扫描。

    想出更高效的办法。你认为多出来的复杂度值得吗？

<!--
2.  How do other languages handle code like this:

    ```lox
    var a = a;
    ```

    What would you do if it was your language? Why?
-->
2.  其他语言如何处理这样的代码：

    ```lox
    var a = a;
    ```

    如果这是你自己的语言，你会怎么做？为什么？

<!--
3.  Many languages make a distinction between variables that can be reassigned
    and those that can't. In Java, the `final` modifier prevents you from
    assigning to a variable. In JavaScript, a variable declared with `let` can
    be assigned, but one declared using `const` can't. Swift treats `let` as
    single-assignment and uses `var` for assignable variables. Scala and Kotlin
    use `val` and `var`.

    Pick a keyword for a single-assignment variable form to add to Lox. Justify
    your choice, then implement it. An attempt to assign to a variable declared
    using your new keyword should cause a compile error.
-->
3.  许多语言区分可以重新赋值的变量与不可以的变量。在 Java 里，`final` 修饰符阻止你给变量赋值；在 JavaScript 里，用 `let` 声明的变量可以赋值，用 `const` 声明的则不行；Swift 把 `let` 当作单次赋值，用 `var` 表示可赋值的变量；Scala 和 Kotlin 则用 `val` 与 `var`。

    挑一个关键字，为 Lox 添加一种单次赋值的变量形式。论证你的选择，然后实现它。试图给用你的新关键字声明的变量赋值，应当引发一个编译错误。

<!--
4.  Extend clox to allow more than 256 local variables to be in scope at a time.
-->
4.  扩展 clox，使其允许同时有超过 256 个局部变量处于作用域内。

</div>
