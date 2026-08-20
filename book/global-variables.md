# 全局变量

<!--
> If only there could be an invention that bottled up a memory, like scent. And
> it never faded, and it never got stale. And then, when one wanted it, the
> bottle could be uncorked, and it would be like living the moment all over
> again.
>
> <cite>Daphne du Maurier, <em>Rebecca</em></cite>
-->
> 要是能有一种发明，把记忆像气味一样装进瓶子里，那该多好啊。它不会褪色，也不会变质。哪天想要了，拔开瓶塞，便能像重新活过那一刻。
>
> <cite>达芙妮·杜穆里埃，<em>《蝴蝶梦》</em></cite>

<!--
The [previous chapter][hash] was a long exploration of one big, deep,
fundamental computer science data structure. Heavy on theory and concept. There
may have been some discussion of big-O notation and algorithms. This chapter has
fewer intellectual pretensions. There are no large ideas to learn. Instead, it's
a handful of straightforward engineering tasks. Once we've completed them, our
virtual machine will support variables.
-->
上一章是对一种庞大、深邃的基础计算机科学数据结构的漫长探索，理论味和概念味都很重。其间或许还夹杂着大 O 记法与算法的讨论。本章则没有那么多学究气——没有什么大思想需要你消化，只是几件直截了当的工程活。做完之后，我们的虚拟机就能支持变量了。

<!--
Actually, it will support only *global* variables. Locals are coming in the
[next chapter][]. In jlox, we managed to cram them both into a single chapter
because we used the same implementation technique for all variables. We built a
chain of environments, one for each scope, all the way up to the top. That was a
simple, clean way to learn how to manage state.
-->
实际上，它支持的*仅仅*是**全局**变量。局部变量留到[下一章][]。在 jlox 里，我们把两者塞进同一章，因为对各类变量用的是同一套实现技巧：搭建一条环境链，每个作用域一层，一路延伸到顶层。那是学习如何管理状态的一种简洁干净的方式。

[next chapter]: local-variables.html

<!--
But it's also *slow*. Allocating a new hash table each time you enter a block or
call a function is not the road to a fast VM. Given how much code is concerned
with using variables, if variables go slow, everything goes slow. For clox,
we'll improve that by using a much more efficient strategy for <span
name="different">local</span> variables, but globals aren't as easily optimized.
-->
但这条路也*慢*得很。每次进入代码块或调用函数都分配一张新哈希表，可不是通往快速虚拟机的康庄大道。代码里有大量篇幅在和变量打交道；变量一慢，一切都慢。对 clox，我们会用高效得多的策略来处理<span name="different">局部</span>变量，但全局变量就没那么容易优化了。

<aside name="different">

<!--
This is a common meta-strategy in sophisticated language implementations. Often,
the same language feature will have multiple implementation techniques, each
tuned for different use patterns. For example, JavaScript VMs often have a
faster representation for objects that are used more like instances of classes
compared to other objects whose set of properties is more freely modified. C and
C++ compilers usually have a variety of ways to compile `switch` statements
based on the number of cases and how densely packed the case values are.
-->
这是成熟语言实现里常见的一种“元策略”：同一语言特性往往有多种实现技巧，各自针对不同的使用模式调优。比如说，JavaScript 虚拟机常常对更像类实例来用的对象，采用比对属性改动更自由的对象更快的表示；C 与 C++ 编译器则通常根据 case 的数量、以及 case 值排得有多密，用好几种方式去编译 `switch` 语句。

</aside>

[hash]: hash-tables.html

<!--
A quick refresher on Lox semantics: Global variables in Lox are "late bound", or
resolved dynamically. This means you can compile a chunk of code that refers to
a global variable before it's defined. As long as the code doesn't *execute*
before the definition happens, everything is fine. In practice, that means you
can refer to later variables inside the body of functions.
-->
先快速复习一下 Lox 的语义：Lox 里的全局变量是“晚绑定”的，或者说动态解析的。这意味着你可以编译一段引用某个全局变量的代码，而那时该变量还没定义——只要代码在定义发生之前*不执行*，一切就没事。实践中，这意味着你可以在函数体里引用后面才定义的变量。

```lox
fun showVariable() {
  print global;
}

var global = "after";
showVariable();
```

<!--
Code like this might seem odd, but it's handy for defining mutually recursive
functions. It also plays nicer with the REPL. You can write a little function in
one line, then define the variable it uses in the next.
-->
这类代码看起来有点怪，但对定义相互递归的函数很方便，跟 REPL 也更合拍：你可以在一行里写个小函数，下一行再定义它用到的变量。

<!--
Local variables work differently. Since a local variable's declaration *always*
occurs before it is used, the VM can resolve them at compile time, even in a
simple single-pass compiler. That will let us use a smarter representation for
locals. But that's for the next chapter. Right now, let's just worry about
globals.
-->
局部变量则不同。局部变量的声明*总是*出现在使用之前，因此即便在简单的单遍编译器里，虚拟机也能在编译期解析它们。这让我们可以为局部变量采用更聪明的表示——但那是下一章的事。眼下，我们只操心全局变量。

<!--
-- Statements
-->
## 语句

<!--
Variables come into being using variable declarations, which means now is also
the time to add support for statements to our compiler. If you recall, Lox
splits statements into two categories. "Declarations" are those statements that
bind a new name to a value. The other kinds of statements -- control flow,
print, etc. -- are just called "statements". We disallow declarations directly
inside control flow statements, like this:
-->
变量通过变量声明诞生，这意味着现在也是时候给编译器加上语句支持了。若你还记得，Lox 把语句分成两类：“声明”是那些把新名字绑定到值的语句；其余种类——控制流、`print` 等等——则统称“语句”。我们不允许声明直接出现在控制流语句里，比如：

```lox
if (monday) var croissant = "yes"; // Error.
```

<!--
Allowing it would raise confusing questions around the scope of the variable.
So, like other languages, we prohibit it syntactically by having a separate
grammar rule for the subset of statements that *are* allowed inside a control
flow body.
-->
允许的话会在变量的作用域上引发一堆让人糊涂的问题。所以，像其他语言一样，我们在语法上禁止它：为允许出现在控制流体内的那部分语句单独设一条文法规则。

```ebnf
statement      → exprStmt
               | forStmt
               | ifStmt
               | printStmt
               | returnStmt
               | whileStmt
               | block ;
```

<!--
Then we use a separate rule for the top level of a script and inside a block.
-->
然后，对脚本顶层和块内部使用另一条规则。

```ebnf
declaration    → classDecl
               | funDecl
               | varDecl
               | statement ;
```

<!--
The `declaration` rule contains the statements that declare names, and also
includes `statement` so that all statement types are allowed. Since `block`
itself is in `statement`, you can put declarations <span
name="parens">inside</span> a control flow construct by nesting them inside a
block.
-->
`declaration` 规则包含那些声明名字的语句，也包含 `statement`，以便允许所有语句类型。由于 `block` 本身在 `statement` 里，你可以通过把声明嵌套在块里，把它们放进控制流结构。

<aside name="parens">

<!--
Blocks work sort of like parentheses do for expressions. A block lets you put
the "lower-precedence" declaration statements in places where only a
"higher-precedence" non-declaring statement is allowed.
-->
块有点像表达式里的括号。块让你能在只允许“高优先级”非声明语句的地方，放入“低优先级”的声明语句。

</aside>

<!--
In this chapter, we'll cover only a couple of statements and one
declaration.
-->
本章我们只覆盖几种语句和一种声明。

```ebnf
statement      → exprStmt
               | printStmt ;

declaration    → varDecl
               | statement ;
```

<!--
Up to now, our VM considered a "program" to be a single expression since that's
all we could parse and compile. In a full Lox implementation, a program is a
sequence of declarations. We're ready to support that now.
-->
此前，我们的 VM 把“程序”当作单个表达式，因为那是我们唯一能解析和编译的东西。在完整的 Lox 实现里，程序是一串声明。我们现在可以支持这个了。

^code compile (1 before, 1 after)

<!--
We keep compiling declarations until we hit the end of the source file. We
compile a single declaration using this:
-->
我们不断编译声明，直到源文件结束。单个声明用下面这个函数编译：

^code declaration

<!--
We'll get to variable declarations later in the chapter, so for now, we simply
forward to `statement()`.
-->
变量声明本章稍后再说，眼下只是转发到 `statement()`。

^code statement

<!--
Blocks can contain declarations, and control flow statements can contain other
statements. That means these two functions will eventually be recursive. We may
as well write out the forward declarations now.
-->
块可以包含声明，控制流语句也可以包含其他语句。这意味着这两个函数最终会递归。不妨现在就把前向声明写出来。

^code forward-declarations (1 before, 1 after)

<!--
### Print statements
-->
### print 语句

<!--
We have two statement types to support in this chapter. Let's start with `print`
statements, which begin, naturally enough, with a `print` token. We detect that
using this helper function:
-->
本章有两种语句要支持。先从 `print` 语句开始——它自然以 `print` 词法单元打头。我们用这个辅助函数检测它：

^code match

<!--
You may recognize it from jlox. If the current token has the given type, we
consume the token and return `true`. Otherwise we leave the token alone and
return `false`. This <span name="turtles">helper</span> function is implemented
in terms of this other helper:
-->
你也许在 jlox 里见过它。若当前词法单元是给定类型，我们就消费该单元并返回 `true`；否则原样保留，返回 `false`。这个<span name="turtles">辅助</span>函数又建立在另一个辅助函数之上：

<aside name="turtles">

<!--
It's helpers all the way down!
-->
辅助函数一层套一层，没有尽头！

</aside>

^code check

<!--
The `check()` function returns `true` if the current token has the given type.
It seems a little <span name="read">silly</span> to wrap this in a function, but
we'll use it more later, and I think short verb-named functions like this make
the parser easier to read.
-->
`check()` 函数在当前词法单元为给定类型时返回 `true`。把它包成函数似乎有点<span name="read">傻</span>，但后面我们会用得更多；我觉得这类短小的动词命名函数，能让解析器更好读。

<aside name="read">

<!--
This sounds trivial, but handwritten parsers for non-toy languages get pretty
big. When you have thousands of lines of code, a utility function that turns two
lines into one and makes the result a little more readable easily earns its
keep.
-->
这听起来微不足道，但手写非玩具语言的解析器，代码量会非常大。当你有成千上万行代码时，一个把两行缩成一行、又让结果更易读一点的工具函数，就值回票价了。

</aside>

<!--
If we did match the `print` token, then we compile the rest of the statement
here:
-->
若确实匹配到了 `print` 词法单元，我们在这里编译语句的其余部分：

^code print-statement

<!--
A `print` statement evaluates an expression and prints the result, so we first
parse and compile that expression. The grammar expects a semicolon after that,
so we consume it. Finally, we emit a new instruction to print the result.
-->
`print` 语句对一个表达式求值并打印结果，所以我们先解析并编译该表达式。文法要求在表达式之后跟分号，于是我们消费它。最后，发射一条新指令来打印结果。

^code op-print (1 before, 1 after)

<!--
At runtime, we execute this instruction like so:
-->
在运行时，我们这样执行该指令：

^code interpret-print (1 before, 1 after)

<!--
When the interpreter reaches this instruction, it has already executed the code
for the expression, leaving the result value on top of the stack. Now we simply
pop and print it.
-->
解释器执行到这条指令时，表达式的代码已经执行完毕，结果值留在栈顶。现在我们只需弹出并打印它。

<!--
Note that we don't push anything else after that. This is a key difference
between expressions and statements in the VM. Every bytecode instruction has a
<span name="effect">**stack effect**</span> that describes how the instruction
modifies the stack. For example, `OP_ADD` pops two values and pushes one,
leaving the stack one element smaller than before.
-->
注意，之后我们不再向栈上推入任何东西。这是 VM 里表达式与语句的一个关键区别。每条字节码指令都有一个<span name="effect">**栈效应**</span>（stack effect），描述该指令如何修改栈。例如，`OP_ADD` 弹出两个值、推入一个，栈比执行前少一个元素。

<aside name="effect">

<!--
The stack is one element shorter after an `OP_ADD`, so its effect is -1:

<img src="image/global-variables/stack-effect.png" alt="The stack effect of an OP_ADD instruction." />
-->
`OP_ADD` 之后栈短了一个元素，所以它的效应是 -1：

<img src="image/global-variables/stack-effect.png" alt="The stack effect of an OP_ADD instruction." />

</aside>

<!--
You can sum the stack effects of a series of instructions to get their total
effect. When you add the stack effects of the series of instructions compiled
from any complete expression, it will total one. Each expression leaves one
result value on the stack.
-->
你可以对一系列指令的栈效应求和，得到它们的总效应。由任意完整表达式编译出的一系列指令，其栈效应总和为 1——每个表达式在栈上留下一个结果值。

<!--
The bytecode for an entire statement has a total stack effect of zero. Since a
statement produces no values, it ultimately leaves the stack unchanged, though
it of course uses the stack while it's doing its thing. This is important
because when we get to control flow and looping, a program might execute a long
series of statements. If each statement grew or shrank the stack, it might
eventually overflow or underflow.
-->
一整条语句的字节码，栈效应总和为零。语句不产生值，最终栈保持不变，尽管执行过程中当然会使用栈。这很重要：等到控制流与循环，程序可能执行一长串语句；若每条语句都让栈变长或变短，栈迟早会溢出或下溢。

<!--
While we're in the interpreter loop, we should delete a bit of code.
-->
趁我们还在解释器循环里，该删掉一点代码了。

^code op-return (1 before, 1 after)

<!--
When the VM only compiled and evaluated a single expression, we had some
temporary code in `OP_RETURN` to output the value. Now that we have statements
and `print`, we don't need that anymore. We're one <span
name="return">step</span> closer to the complete implementation of clox.
-->
当 VM 只编译并求值单个表达式时，我们在 `OP_RETURN` 里放了些临时代码来输出该值。现在我们有了语句和 `print`，不再需要那些了。我们离 clox 的完整实现又近了一<span name="return">步</span>。

<aside name="return">

<!--
We're only one step closer, though. We will revisit `OP_RETURN` again when we
add functions. Right now, it exits the entire interpreter loop.
-->
不过，只是近了一步。加上函数之后，我们还会再审视 `OP_RETURN`。眼下，它退出整个解释器循环。

</aside>

<!--
As usual, a new instruction needs support in the disassembler.
-->
照例，新指令也需要反汇编器的支持。

^code disassemble-print (1 before, 1 after)

<!--
That's our `print` statement. If you want, give it a whirl:
-->
`print` 语句就这些。若你愿意，可以试一下：

```lox
print 1 + 2;
print 3 * 4;
```

<!--
Exciting! OK, maybe not thrilling, but we can build scripts that contain as many
statements as we want now, which feels like progress.
-->
激动人心！好吧，也许谈不上热血沸腾，但我们终于可以写出想写多少条语句就写多少条的脚本了，这感觉像是一种进步。

<!--
### Expression statements
-->
### 表达式语句

<!--
Wait until you see the next statement. If we *don't* see a `print` keyword, then
we must be looking at an expression statement.
-->
等着看下一类语句吧。若没看到 `print` 关键字，那一定是表达式语句。

^code parse-expressions-statement (1 before, 1 after)

<!--
It's parsed like so:
-->
解析方式如下：

^code expression-statement

<!--
An "expression statement" is simply an expression followed by a semicolon.
They're how you write an expression in a context where a statement is expected.
Usually, it's so that you can call a function or evaluate an assignment for its
side effect, like this:
-->
“表达式语句”就是一个表达式后面跟分号。它让你在期望语句的上下文中写表达式——通常是为了调用函数，或为了副作用而对赋值表达式求值，比如：

```lox
brunch = "quiche";
eat(brunch);
```

<!--
Semantically, an expression statement evaluates the expression and discards the
result. The compiler directly encodes that behavior. It compiles the expression,
and then emits an `OP_POP` instruction.
-->
在语义上，表达式语句对表达式求值，然后丢弃结果。编译器直接编码这种行为：编译表达式，然后发射 `OP_POP` 指令。

^code pop-op (1 before, 1 after)

<!--
As the name implies, that instruction pops the top value off the stack and
forgets it.
-->
顾名思义，该指令弹出栈顶值并忘掉它。

^code interpret-pop (1 before, 1 after)

<!--
We can disassemble it too.
-->
反汇编也可以做。

^code disassemble-pop (1 before, 1 after)

<!--
Expression statements aren't very useful yet since we can't create any
expressions that have side effects, but they'll be essential when we
[add functions later][functions]. The <span name="majority">majority</span> of
statements in real-world code in languages like C are expression statements.
-->
表达式语句眼下还不太有用，因为我们还写不出有副作用的表达式；但等到[后面加上函数][functions]，它们就必不可少了。C 之类语言里，真实代码中的语句<span name="majority">绝大多数</span>都是表达式语句。

<aside name="majority">

<!--
By my count, 80 of the 149 statements, in the version of "compiler.c" that we
have at the end of this chapter are expression statements.
-->
我数了一下，本章结束时那份 `compiler.c` 的 149 条语句里，有 80 条是表达式语句。

</aside>

[functions]: calls-and-functions.html

<!--
### Error synchronization
-->
### 错误同步

<!--
While we're getting this initial work done in the compiler, we can tie off a
loose end we left [several chapters back][errors]. Like jlox, clox uses panic
mode error recovery to minimize the number of cascaded compile errors that it
reports. The compiler exits panic mode when it reaches a synchronization point.
For Lox, we chose statement boundaries as that point. Now that we have
statements, we can implement synchronization.
-->
趁我们在编译器里做这批初始工作，可以把[几章之前][errors]留下的一截线头收束掉。与 jlox 一样，clox 使用恐慌模式错误恢复，尽量减少级联编译错误的报告数量。编译器到达同步点时退出恐慌模式。对 Lox，我们选语句边界作为那个点。现在我们有了语句，可以实现同步了。

[errors]: compiling-expressions.html#handling-syntax-errors

^code call-synchronize (1 before, 1 after)

<!--
If we hit a compile error while parsing the previous statement, we enter panic
mode. When that happens, after the statement we start synchronizing.
-->
若在解析上一条语句时碰到编译错误，我们进入恐慌模式。此时，在该语句之后开始同步。

^code synchronize

<!--
We skip tokens indiscriminately until we reach something that looks like a
statement boundary. We recognize the boundary by looking for a preceding token
that can end a statement, like a semicolon. Or we'll look for a subsequent token
that begins a statement, usually one of the control flow or declaration
keywords.
-->
我们无差别地跳过词法单元，直到遇到看起来像语句边界的东西。我们通过寻找能结束语句的前导词法单元来识别边界，比如分号；或者寻找能开始语句的后续词法单元，通常是控制流或声明关键字之一。

<!--
-- Variable Declarations
-->
## 变量声明

<!--
Merely being able to *print* doesn't win your language any prizes at the
programming language <span name="fair">fair</span>, so let's move on to
something a little more ambitious and get variables going. There are three
operations we need to support:
-->
仅仅能*打印*，在程序语言<span name="fair">博览会</span>上可赢不了奖，所以让我们做点更雄心勃勃的事——把变量搞起来。需要支持三种操作：

<aside name="fair">

<!--
I can't help but imagine a "language fair" like some country 4H thing. Rows of
straw-lined stalls full of baby languages *moo*ing and *baa*ing at each other.
-->
我忍不住想象一种“语言博览会”，像乡下 4H 活动那样：一排排铺着稻草的摊位，满是小语言彼此 *moo*、*baa* 地叫。

</aside>

<!--
*   Declaring a new variable using a `var` statement.
*   Accessing the value of a variable using an identifier expression.
*   Storing a new value in an existing variable using an assignment expression.
-->
*   用 `var` 语句声明新变量。
*   用标识符表达式访问变量的值。
*   用赋值表达式给已有变量存新值。

<!--
We can't do either of the last two until we have some variables, so we start
with declarations.
-->
后两种在还没有变量之前都做不了，所以我们从声明开始。

^code match-var (1 before, 2 after)

<!--
The placeholder parsing function we sketched out for the declaration grammar
rule has an actual production now. If we match a `var` token, we jump here:
-->
我们为声明文法规则草拟的占位解析函数，现在有了真正的产生式。若匹配到 `var` 词法单元，就跳到这里：

^code var-declaration

<!--
The keyword is followed by the variable name. That's compiled by
`parseVariable()`, which we'll get to in a second. Then we look for an `=`
followed by an initializer expression. If the user doesn't initialize the
variable, the compiler implicitly initializes it to <span
name="nil">`nil`</span> by emitting an `OP_NIL` instruction. Either way, we
expect the statement to be terminated with a semicolon.
-->
关键字后面是变量名，由 `parseVariable()` 编译——我们马上会讲到。然后查找 `=` 及其后的初始化表达式。若用户没有初始化变量，编译器会发射 `OP_NIL` 指令，隐式把变量初始化为 <span name="nil">`nil`</span>。无论哪种情况，我们都期望语句以分号结束。

<aside name="nil" class="bottom">

<!--
Essentially, the compiler desugars a variable declaration like:

```lox
var a;
```

into:

```lox
var a = nil;
```

The code it generates for the former is identical to what it produces for the
latter.
-->
本质上，编译器把这样的变量声明：

```lox
var a;
```

脱糖成：

```lox
var a = nil;
```

前者生成的代码与后者完全相同。

</aside>

<!--
There are two new functions here for working with variables and identifiers.
Here is the first:
-->
这里有两个处理变量与标识符的新函数。第一个是：

^code parse-variable (2 before)

<!--
It requires the next token to be an identifier, which it consumes and sends
here:
-->
它要求下一个词法单元是标识符，消费它，然后送到这里：

^code identifier-constant (2 before)

<!--
This function takes the given token and adds its lexeme to the chunk's constant
table as a string. It then returns the index of that constant in the constant
table.
-->
该函数接受给定的词法单元，把其词素作为字符串加入 chunk 的常量表，然后返回该常量在常量表中的索引。

<!--
Global variables are looked up *by name* at runtime. That means the VM -- the
bytecode interpreter loop -- needs access to the name. A whole string is too big
to stuff into the bytecode stream as an operand. Instead, we store the string in
the constant table and the instruction then refers to the name by its index in
the table.
-->
全局变量在运行时*按名字*查找。这意味着 VM——字节码解释器循环——需要访问名字。整段字符串太大，塞不进字节码流作为操作数。我们把字符串存在常量表里，指令再通过表中的索引引用该名字。

<!--
This function returns that index all the way to `varDeclaration()` which later
hands it over to here:
-->
该函数把索引一路返回给 `varDeclaration()`，后者再把它交给这里：

^code define-variable

<!--
<span name="helper">This</span> outputs the bytecode instruction that defines
the new variable and stores its initial value. The index of the variable's name
in the constant table is the instruction's operand. As usual in a stack-based
VM, we emit this instruction last. At runtime, we execute the code for the
variable's initializer first. That leaves the value on the stack. Then this
instruction takes that value and stores it away for later.
-->
<span name="helper">这</span>条路径输出定义新变量并存储其初始值的字节码指令。变量名在常量表中的索引就是该指令的操作数。与栈式 VM 的惯例一样，我们最后才发射这条指令：运行时先执行变量初始化器的代码，值留在栈上；然后这条指令把该值取走存起来，留待后用。

<aside name="helper">

<!--
I know some of these functions seem pretty pointless right now. But we'll get
more mileage out of them as we add more language features for working with
names. Function and class declarations both declare new variables, and variable
and assignment expressions access them.
-->
我知道有些函数眼下看起来相当多余。但等我们加上更多与名字打交道的语言特性，它们会派上更大用场。函数与类声明都会声明新变量，变量与赋值表达式则访问它们。

</aside>

<!--
Over in the runtime, we begin with this new instruction:
-->
在运行时一侧，我们从这条新指令开始：

^code define-global-op (1 before, 1 after)

<!--
Thanks to our handy-dandy hash table, the implementation isn't too hard.
-->
多亏我们顺手的哈希表，实现并不太难。

^code interpret-define-global (1 before, 1 after)

<!--
We get the name of the variable from the constant table. Then we <span
name="pop">take</span> the value from the top of the stack and store it in a
hash table with that name as the key.
-->
我们从常量表取出变量名，然后<span name="pop">取</span>栈顶的值，以该名为键存入哈希表。

<aside name="pop">

<!--
Note that we don't *pop* the value until *after* we add it to the hash table.
That ensures the VM can still find the value if a garbage collection is
triggered right in the middle of adding it to the hash table. That's a distinct
possibility since the hash table requires dynamic allocation when it resizes.
-->
注意，我们是在把值加入哈希表*之后*才*弹出*它。这确保若在加入哈希表的过程中触发了垃圾回收，VM 仍能找到该值——哈希表在扩容时需要动态分配，这完全可能发生。

</aside>

<!--
This code doesn't check to see if the key is already in the table. Lox is pretty
lax with global variables and lets you redefine them without error. That's
useful in a REPL session, so the VM supports that by simply overwriting the
value if the key happens to already be in the hash table.
-->
这段代码不检查键是否已在表中。Lox 对全局变量相当宽松，允许你重新定义而不报错。在 REPL 会话里这很有用，所以 VM 在键已存在时直接覆写值。

<!--
There's another little helper macro:
-->
还有一个小辅助宏：

^code read-string (1 before, 1 after)

<!--
It reads a one-byte operand from the bytecode chunk. It treats that as an index
into the chunk's constant table and returns the string at that index. It doesn't
check that the value *is* a string -- it just indiscriminately casts it. That's
safe because the compiler never emits an instruction that refers to a non-string
constant.
-->
它从字节码 chunk 读取一字节操作数，当作 chunk 常量表的索引，返回该索引处的字符串。它不检查该值*是否*为字符串——直接强转。这安全，因为编译器从不发射引用非字符串常量的指令。

<!--
Because we care about lexical hygiene, we also undefine this macro at the end of
the interpret function.
-->
因为我们讲究词法卫生，在 interpret 函数末尾也会取消定义这个宏。

^code undef-read-string (1 before, 1 after)

<!--
I keep saying "the hash table", but we don't actually have one yet. We need a
place to store these globals. Since we want them to persist as long as clox is
running, we store them right in the VM.
-->
我老说“那张哈希表”，其实我们还没有。我们需要地方存这些全局变量。既然希望它们在 clox 运行期间一直存在，就把它们直接存在 VM 里。

^code vm-globals (1 before, 1 after)

<!--
As we did with the string table, we need to initialize the hash table to a valid
state when the VM boots up.
-->
与字符串表一样，VM 启动时要把哈希表初始化到有效状态。

^code init-globals (1 before, 1 after)

<!--
And we <span name="tear">tear</span> it down when we exit.
-->
退出时我们<span name="tear">拆</span>掉它。

<aside name="tear">

<!--
The process will free everything on exit, but it feels undignified to require
the operating system to clean up our mess.
-->
进程退出时会释放一切，但让操作系统来收拾我们的烂摊子，总觉得不太体面。

</aside>

^code free-globals (1 before, 1 after)

<!--
As usual, we want to be able to disassemble the new instruction too.
-->
照例，新指令也要能反汇编。

^code disassemble-define-global (1 before, 1 after)

<!--
And with that, we can define global variables. Not that users can *tell* that
they've done so, because they can't actually *use* them. So let's fix that next.
-->
至此，我们可以定义全局变量了——不过用户还*感觉*不到，因为他们实际上还*用*不了。接下来把它补上。

<!--
-- Reading Variables
-->
## 读取变量

<!--
As in every programming language ever, we access a variable's value using its
name. We hook up identifier tokens to the expression parser here:
-->
与有史以来每一门程序语言一样，我们用名字访问变量的值。在这里把标识符词法单元挂到表达式解析器上：

^code table-identifier (1 before, 1 after)

<!--
That calls this new parser function:
-->
它会调用这个新的解析函数：

^code variable-without-assign

<!--
Like with declarations, there are a couple of tiny helper functions that seem
pointless now but will become more useful in later chapters. I promise.
-->
与声明一样，有几个小辅助函数眼下看似多余，后面章节会更有用。我保证。

^code read-named-variable

<!--
This calls the same `identifierConstant()` function from before to take the
given identifier token and add its lexeme to the chunk's constant table as a
string. All that remains is to emit an instruction that loads the global
variable with that name. Here's the instruction:
-->
它调用之前的 `identifierConstant()`，把给定标识符词法单元的词素作为字符串加入 chunk 常量表。剩下只需发射一条指令，加载该名字的全局变量。指令如下：

^code get-global-op (1 before, 1 after)

<!--
Over in the interpreter, the implementation mirrors `OP_DEFINE_GLOBAL`.
-->
在解释器里，实现与 `OP_DEFINE_GLOBAL` 镜像对称。

^code interpret-get-global (1 before, 1 after)

<!--
We pull the constant table index from the instruction's operand and get the
variable name. Then we use that as a key to look up the variable's value in the
globals hash table.
-->
我们从指令操作数取出常量表索引，得到变量名，再以它为键在全局哈希表里查找变量的值。

<!--
If the key isn't present in the hash table, it means that global variable has
never been defined. That's a runtime error in Lox, so we report it and exit the
interpreter loop if that happens. Otherwise, we take the value and push it
onto the stack.
-->
若键不在哈希表里，说明该全局变量从未被定义。在 Lox 里这是运行时错误，我们会报告并退出解释器循环。否则，取该值推入栈。

^code disassemble-get-global (1 before, 1 after)

<!--
A little bit of disassembling, and we're done. Our interpreter is now able to
run code like this:
-->
再补一点反汇编，就完成了。解释器现在能运行这样的代码：

```lox
var beverage = "cafe au lait";
var breakfast = "beignets with " + beverage;
print breakfast;
```

<!--
There's only one operation left.
-->
只剩一种操作了。

<!--
-- Assignment
-->
## 赋值

<!--
Throughout this book, I've tried to keep you on a fairly safe and easy path. I
don't avoid hard *problems*, but I try to not make the *solutions* more complex
than they need to be. Alas, other design choices in our <span
name="jlox">bytecode</span> compiler make assignment annoying to implement.
-->
全书下来，我尽量让你走在相对安全、轻松的路上。难*问题*我不躲，但尽量不把*解法*弄得比必要更绕。可惜啊，我们<span name="jlox">字节码</span>编译器里的另一些设计选择，偏偏让赋值变得挺烦人。

<aside name="jlox">

<!--
If you recall, assignment was pretty easy in jlox.
-->
若你记得，赋值在 jlox 里相当简单。

</aside>

<!--
Our bytecode VM uses a single-pass compiler. It parses and generates bytecode
on the fly without any intermediate AST. As soon as it recognizes a piece of
syntax, it emits code for it. Assignment doesn't naturally fit that. Consider:
-->
我们的字节码虚拟机用的是单遍编译器：边解析边生成字节码，中间不经过 AST。一认出某段语法，就立刻为它发射代码。赋值天然跟这种模式不太合得来。比方说：

```lox
menu.brunch(sunday).beverage = "mimosa";
```

<!--
In this code, the parser doesn't realize `menu.brunch(sunday).beverage` is the
target of an assignment and not a normal expression until it reaches `=`, many
tokens after the first `menu`. By then, the compiler has already emitted
bytecode for the whole thing.
-->
在这段代码里，解析器直到遇见 `=`——在第一个 `menu` 之后很多个词法单元——才意识到 `menu.brunch(sunday).beverage` 是赋值目标而非普通表达式。到那时，编译器已经为整段东西发射了字节码。

<!--
The problem is not as dire as it might seem, though. Look at how the parser sees that example:
-->
问题倒没有看起来那么严重。看看解析器如何看那个例子：

<img src="image/global-variables/setter.png" alt="The 'menu.brunch(sunday).beverage = &quot;mimosa&quot;' statement, showing that 'menu.brunch(sunday)' is an expression." />

<!--
Even though the `.beverage` part must not be compiled as a get expression,
everything to the left of the `.` is an expression, with the normal expression
semantics. The `menu.brunch(sunday)` part can be compiled and executed as usual.
-->
虽然 `.beverage` 部分不能按 get 表达式编译，但 `.` 左边的所有东西都是表达式，具有普通表达式语义。`menu.brunch(sunday)` 部分可以照常编译和执行。

<!--
Fortunately for us, the only semantic differences on the left side of an
assignment appear at the very right-most end of the tokens, immediately
preceding the `=`. Even though the receiver of a setter may be an arbitrarily
long expression, the part whose behavior differs from a get expression is only
the trailing identifier, which is right before the `=`. We don't need much
lookahead to realize `beverage` should be compiled as a set expression and not a
getter.
-->
对我们来说幸运的是，赋值左侧唯一的语义差异出现在词法单元序列的最右端，紧挨 `=` 之前。尽管 setter 的接收者可以是任意长的表达式，行为与 get 表达式不同的部分只是末尾的标识符，就在 `=` 前面。我们不需要太多前瞻，就能意识到 `beverage` 该按 set 表达式编译，而不是 getter。

<!--
Variables are even easier since they are just a single bare identifier before an
`=`. The idea then is that right *before* compiling an expression that can also
be used as an assignment target, we look for a subsequent `=` token. If we see
one, we compile it as an assignment or setter instead of a variable access or
getter.
-->
变量更简单，因为 `=` 前面只是一个裸标识符。思路是：在编译一个*也*能用作赋值目标的表达式*之前*，先查找后面是否有 `=` 词法单元。若有，就按赋值或 setter 编译，而不是变量访问或 getter。

<!--
We don't have setters to worry about yet, so all we need to handle are variables.
-->
我们还没有 setter 要操心，所以只需处理变量。

^code named-variable (1 before, 1 after)

<!--
In the parse function for identifier expressions, we look for an equals sign
after the identifier. If we find one, instead of emitting code for a variable
access, we compile the assigned value and then emit an assignment instruction.
-->
在标识符表达式的解析函数里，我们在标识符之后查找等号。若找到，就不发射变量访问的代码，而是编译被赋的值，然后发射赋值指令。

<!--
That's the last instruction we need to add in this chapter.
-->
这是本章要加的最后一条指令。

^code set-global-op (1 before, 1 after)

<!--
As you'd expect, its runtime behavior is similar to defining a new variable.
-->
如你所料，其运行时行为与定义新变量类似。

^code interpret-set-global (1 before, 1 after)

<!--
The main difference is what happens when the key doesn't already exist in the
globals hash table. If the variable hasn't been defined yet, it's a runtime
error to try to assign to it. Lox [doesn't do implicit variable
declaration][implicit].
-->
主要区别在于键尚不在全局哈希表里时会发生什么。若变量尚未定义，试图赋值是运行时错误。Lox [不做隐式变量声明][implicit]。

<aside name="delete">

<!--
The call to `tableSet()` stores the value in the global variable table even if
the variable wasn't previously defined. That fact is visible in a REPL session,
since it keeps running even after the runtime error is reported. So we also take
care to delete that zombie value from the table.
-->
`tableSet()` 的调用会把值存进全局变量表，即便变量先前未定义。在 REPL 会话里这一点可见，因为报告运行时错误后 REPL 仍继续运行。所以我们还要从表里删掉那个僵尸值。

</aside>

<!--
The other difference is that setting a variable doesn't pop the value off the
stack. Remember, assignment is an expression, so it needs to leave that value
there in case the assignment is nested inside some larger expression.
-->
另一个区别是，给变量赋值不会把值从栈上弹出。记住，赋值是表达式，若赋值嵌在更大的表达式里，需要把该值留在栈上。

[implicit]: statements-and-state.html#design-note

<!--
Add a dash of disassembly:
-->
再加点反汇编：

^code disassemble-set-global (2 before, 1 after)

<!--
So we're done, right? Well... not quite. We've made a mistake! Take a gander at:
-->
那我们完成了，对吧？嗯……还没。我们犯了个错！看看这个：

```lox
a * b = c + d;
```

<!--
According to Lox's grammar, `=` has the lowest precedence, so this should be
parsed roughly like:
-->
按 Lox 文法，`=` 优先级最低，所以大致应解析成：

<img src="image/global-variables/ast-good.png" alt="The expected parse, like '(a * b) = (c + d)'." />

<!--
Obviously, `a * b` isn't a <span name="do">valid</span> assignment target, so
this should be a syntax error. But here's what our parser does:
-->
显然，`a * b` 不是合法的<span name="do">赋值</span>目标，这应该是语法错误。但我们的解析器实际做的是：

<aside name="do">

<!--
Wouldn't it be wild if `a * b` *was* a valid assignment target, though? You
could imagine some algebra-like language that tried to divide the assigned value
up in some reasonable way and distribute it to `a` and `b`... that's probably
a terrible idea.
-->
要是 `a * b` *真是*合法的赋值目标，那岂不是很疯狂？你可以想象某种代数式语言，试图把被赋的值合理拆分、分发到 `a` 和 `b`……那大概是个糟糕的主意。

</aside>

<!--
1.  First, `parsePrecedence()` parses `a` using the `variable()` prefix parser.
1.  After that, it enters the infix parsing loop.
1.  It reaches the `*` and calls `binary()`.
1.  That recursively calls `parsePrecedence()` to parse the right-hand operand.
1.  That calls `variable()` again for parsing `b`.
1.  Inside that call to `variable()`, it looks for a trailing `=`. It sees one
    and thus parses the rest of the line as an assignment.
-->
1.  首先，`parsePrecedence()` 用 `variable()` 前缀解析器解析 `a`。
1.  然后进入中缀解析循环。
1.  遇到 `*`，调用 `binary()`。
1.  它递归调用 `parsePrecedence()` 解析右操作数。
1.  再次调用 `variable()` 解析 `b`。
1.  在 `variable()` 内部查找尾随的 `=`，找到了，于是把该行剩余部分当作赋值解析。

<!--
In other words, the parser sees the above code like:
-->
换句话说，解析器把上面的代码看成：

<img src="image/global-variables/ast-bad.png" alt="The actual parse, like 'a * (b = c + d)'." />

<!--
We've messed up the precedence handling because `variable()` doesn't take into
account the precedence of the surrounding expression that contains the variable.
If the variable happens to be the right-hand side of an infix operator, or the
operand of a unary operator, then that containing expression is too high
precedence to permit the `=`.
-->
我们搞砸了优先级处理，因为 `variable()` 没有考虑包含该变量的外围表达式的优先级。若变量碰巧是中缀运算符的右操作数，或一元运算符的操作数，那包含它的表达式优先级太高，不允许 `=`。

<!--
To fix this, `variable()` should look for and consume the `=` only if it's in
the context of a low-precedence expression. The code that knows the current
precedence is, logically enough, `parsePrecedence()`. The `variable()` function
doesn't need to know the actual level. It just cares that the precedence is low
enough to allow assignment, so we pass that fact in as a Boolean.
-->
要修复这一点，`variable()` 应只在低优先级表达式的上下文中查找并消费 `=`。知道当前优先级的是 `parsePrecedence()`——逻辑上本该如此。`variable()` 不需要知道具体级别，只关心优先级是否低到允许赋值，所以我们把这个事实作为布尔值传进去。

^code prefix-rule (4 before, 2 after)

<!--
Since assignment is the lowest-precedence expression, the only time we allow an
assignment is when parsing an assignment expression or top-level expression like
in an expression statement. That flag makes its way to the parser function here:
-->
赋值是优先级最低的表达式，因此只有解析赋值表达式或顶层表达式（比如表达式语句里的）时才允许赋值。该标志一路传到这里的解析函数：

^code variable

<!--
Which passes it through a new parameter:
-->
再通过新参数传下去：

^code named-variable-signature (1 after)

<!--
And then finally uses it here:
-->
最终在这里使用：

^code named-variable-can-assign (2 before, 1 after)

<!--
That's a lot of plumbing to get literally one bit of data to the right place in
the compiler, but arrived it has. If the variable is nested inside some
expression with higher precedence, `canAssign` will be `false` and this will
ignore the `=` even if there is one there. Then `namedVariable()` returns, and
execution eventually makes its way back to `parsePrecedence()`.
-->
为了把一位数据送到编译器里正确的位置，管线工程可真不少——但总算送到了。若变量嵌在更高优先级表达式里，`canAssign` 为 `false`，即使有 `=` 也会忽略。然后 `namedVariable()` 返回，执行最终回到 `parsePrecedence()`。

<!--
Then what? What does the compiler do with our broken example from before? Right
now, `variable()` won't consume the `=`, so that will be the current token. The
compiler returns back to `parsePrecedence()` from the `variable()` prefix parser
and then tries to enter the infix parsing loop. There is no parsing function
associated with `=`, so it skips that loop.
-->
然后呢？编译器对我们之前那个坏例子怎么办？现在 `variable()` 不会消费 `=`，于是它成为当前词法单元。编译器从 `variable()` 前缀解析器回到 `parsePrecedence()`，然后试图进入中缀解析循环。没有与 `=` 关联的解析函数，于是跳过该循环。

<!--
Then `parsePrecedence()` silently returns back to the caller. That also isn't
right. If the `=` doesn't get consumed as part of the expression, nothing else
is going to consume it. It's an error and we should report it.
-->
然后 `parsePrecedence()` 静默返回给调用者。这也不对。若 `=` 没有作为表达式的一部分被消费，就没有别的东西会消费它。这是错误，我们应该报告。

^code invalid-assign (2 before, 1 after)

<!--
With that, the previous bad program correctly gets an error at compile time. OK,
*now* are we done? Still not quite. See, we're passing an argument to one of the
parse functions. But those functions are stored in a table of function pointers,
so all of the parse functions need to have the same type. Even though most parse
functions don't support being used as an assignment target -- setters are the
<span name="index">only</span> other one -- our friendly C compiler requires
them *all* to accept the parameter.
-->
这样，之前那个坏程序会在编译期正确报错。好，*现在*完成了吗？还没。你看，我们给某个解析函数传了参数。但这些函数存在函数指针表里，所以所有解析函数必须有相同类型。尽管大多数解析函数不支持被用作赋值目标——setter 是<span name="index">唯一</span>的其他情况——友好的 C 编译器仍要求它们*全部*接受该参数。

<aside name="index">

<!--
If Lox had arrays and subscript operators like `array[index]` then an infix `[`
would also allow assignment to support `array[index] = value`.
-->
若 Lox 有数组和下标运算符如 `array[index]`，中缀 `[` 也会允许赋值，以支持 `array[index] = value`。

</aside>

<!--
So we're going to finish off this chapter with some grunt work. First, let's go
ahead and pass the flag to the infix parse functions.
-->
所以我们用些体力活收束本章。首先，把标志传给中缀解析函数。

^code infix-rule (1 before, 1 after)

<!--
We'll need that for setters eventually. Then we'll fix the typedef for the
function type.
-->
setter 迟早会用到。然后修正函数类型的 typedef。

^code parse-fn-type (2 before, 2 after)

<!--
And some completely tedious code to accept this parameter in all of our existing
parse functions. Here:
-->
接着是完全繁琐的代码，让所有现有解析函数接受这个参数。这里：

^code binary (1 after)

<!--
And here:
-->
这里：

^code parse-literal (1 after)

<!--
And here:
-->
这里：

^code grouping (1 after)

<!--
And here:
-->
这里：

^code number (1 after)

<!--
And here too:
-->
还有这里：

^code string (1 after)

<!--
And, finally:
-->
最后：

^code unary (1 after)

<!--
Phew! We're back to a C program we can compile. Fire it up and now you can run
this:
-->
呼！我们又回到可以编译的 C 程序了。启动它，现在可以运行：

```lox
var breakfast = "beignets";
var beverage = "cafe au lait";
breakfast = "beignets with " + beverage;

print breakfast;
```

<!--
It's starting to look like real code for an actual language!
-->
开始有点像一门真正语言里的真实代码了！

<div class="challenges">

<!--
## Challenges
-->
## 挑战

<!--
1.  The compiler adds a global variable's name to the constant table as a string
    every time an identifier is encountered. It creates a new constant each
    time, even if that variable name is already in a previous slot in the
    constant table. That's wasteful in cases where the same variable is
    referenced multiple times by the same function. That, in turn, increases the
    odds of filling up the constant table and running out of slots since we
    allow only 256 constants in a single chunk.

    Optimize this. How does your optimization affect the performance of the
    compiler compared to the runtime? Is this the right trade-off?
-->
1.  编译器每次遇到标识符，都会把全局变量名作为字符串加入常量表。即便该变量名已在常量表先前的槽位里，它也会每次创建新常量。同一函数多次引用同一变量时，这很浪费；而我们每个 chunk 只允许 256 个常量，这还会增加常量表填满、槽位用尽的几率。

    优化这一点。你的优化如何影响编译器性能与运行时性能？这是正确的权衡吗？

<!--
2.  Looking up a global variable by name in a hash table each time it is used
    is pretty slow, even with a good hash table. Can you come up with a more
    efficient way to store and access global variables without changing the
    semantics?
-->
2.  每次使用全局变量都在哈希表里按名字查找，即便哈希表很好，也相当慢。你能想出更高效地存储和访问全局变量的方法，而不改变语义吗？

<!--
3.  When running in the REPL, a user might write a function that references an
    unknown global variable. Then, in the next line, they declare the variable.
    Lox should handle this gracefully by not reporting an "unknown variable"
    compile error when the function is first defined.

    But when a user runs a Lox *script*, the compiler has access to the full
    text of the entire program before any code is run. Consider this program:

    ```lox
    fun useVar() {
      print oops;
    }

    var ooops = "too many o's!";
    ```

    Here, we can tell statically that `oops` will not be defined because there
    is *no* declaration of that global anywhere in the program. Note that
    `useVar()` is never called either, so even though the variable isn't
    defined, no runtime error will occur because it's never used either.

    We could report mistakes like this as compile errors, at least when running
    from a script. Do you think we should? Justify your answer. What do other
    scripting languages you know do?
-->
3.  在 REPL 里，用户可能写了一个引用未知全局变量的函数，下一行再声明该变量。Lox 应优雅处理：在函数首次定义时不报告“未知变量”编译错误。

    但用户运行 Lox *脚本*时，编译器在任何代码运行之前就能访问整个程序的完整文本。考虑这个程序：

    ```lox
    fun useVar() {
      print oops;
    }

    var ooops = "too many o's!";
    ```

    这里我们可以静态判断 `oops` 不会被定义，因为程序里*没有*该全局变量的声明。注意 `useVar()` 也从未被调用，所以即便变量未定义，也不会发生运行时错误，因为它从未被使用。

    我们至少可以在运行脚本时，把这类错误报告为编译错误。你认为应该吗？论证你的答案。你了解的其他脚本语言怎么做？

</div>
