# 来回跳转

<!--
> The order that our mind imagines is like a net, or like a ladder, built to
> attain something. But afterward you must throw the ladder away, because you
> discover that, even if it was useful, it was meaningless.
>
> <cite>Umberto Eco, <em>The Name of the Rose</em></cite>
-->
> 我们心中构想的秩序像一张网，或像一架梯子，为抵达某物而搭起。但事后你必须把梯子扔掉，因为你会发现：即便它曾有用，它也毫无意义。
>
> <cite>翁贝托·埃科，<em>《玫瑰的名字》</em></cite>

<!--
It's taken a while to get here, but we're finally ready to add control flow to
our virtual machine. In the tree-walk interpreter we built for jlox, we
implemented Lox's control flow in terms of Java's. To execute a Lox `if`
statement, we used a Java `if` statement to run the chosen branch. That works,
but isn't entirely satisfying. By what magic does the *JVM itself* or a native
CPU implement `if` statements? Now that we have our own bytecode VM to hack on,
we can answer that.
-->
走到这儿花了不少时间，但我们终于可以给虚拟机加上控制流了。在为 jlox 搭建的树遍历解释器里，我们用 Java 的控制流来实现 Lox 的控制流。要执行一条 Lox `if` 语句，就用一条 Java `if` 去跑选中的分支。能用，却不完全令人满意。*JVM 本身*或原生 CPU，究竟靠什么魔法实现 `if`？如今我们有自己的字节码虚拟机可以折腾，就能回答这个问题了。

<!--
When we talk about "control flow", what are we referring to? By "flow" we mean
the way execution moves through the text of the program. Almost like there is a
little robot inside the computer wandering through our code, executing bits and
pieces here and there. Flow is the path that robot takes, and by *controlling*
the robot, we drive which pieces of code it executes.
-->
我们说的“控制流”，到底指什么？所谓“流”，是指执行如何穿过程序的文本。几乎像电脑里有个小机器人，在我们的代码里游荡，这儿执行一点、那儿执行一点。流，就是那机器人走的路径；通过*控制*它，我们决定它执行哪些代码片段。

<!--
In jlox, the robot's locus of attention -- the *current* bit of code -- was
implicit based on which AST nodes were stored in various Java variables and what
Java code we were in the middle of running. In clox, it is much more explicit.
The VM's `ip` field stores the address of the current bytecode instruction. The
value of that field is exactly "where we are" in the program.
-->
在 jlox 里，机器人的注意力焦点——*当前*那段代码——是隐式的：取决于各 Java 变量里存着哪些 AST 节点，以及我们正跑到哪段 Java 代码。在 clox 里则显式得多。虚拟机的 `ip` 字段存着当前字节码指令的地址。该字段的值，正是我们在程序里“身在何处”。

<!--
Execution proceeds normally by incrementing the `ip`. But we can mutate that
variable however we want to. In order to implement control flow, all that's
necessary is to change the `ip` in more interesting ways. The simplest control
flow construct is an `if` statement with no `else` clause:
-->
正常执行靠递增 `ip`。但我们可以随意改写那个变量。要实现控制流，所需要的不过是用更有趣的方式改动 `ip`。最简单的控制流构造，是没有 `else` 子句的 `if` 语句：

```lox
if (condition) print("condition was truthy");
```

<!--
The VM evaluates the bytecode for the condition expression. If the result is
truthy, then it continues along and executes the `print` statement in the body.
The interesting case is when the condition is falsey. When that happens,
execution skips over the then branch and proceeds to the next statement.
-->
虚拟机先求值条件表达式的字节码。若结果为真值，就继续往下，执行体里的 `print` 语句。有意思的是条件为假值时：执行会跳过 then 分支，直接走到下一条语句。

<!--
To skip over a chunk of code, we simply set the `ip` field to the address of the
bytecode instruction following that code. To *conditionally* skip over some
code, we need an instruction that looks at the value on top of the stack. If
it's falsey, it adds a given offset to the `ip` to jump over a range of
instructions. Otherwise, it does nothing and lets execution proceed to the next
instruction as usual.
-->
要跳过一块代码，只需把 `ip` 设成那段代码之后那条字节码指令的地址。要*有条件地*跳过一些代码，我们需要一条指令：查看栈顶的值；若为假值，就把给定偏移加到 `ip` 上，跳过一段指令；否则什么也不做，让执行像往常一样落到下一条指令。

<!--
When we compile to bytecode, the explicit nested block structure of the code
evaporates, leaving only a flat series of instructions behind. Lox is a
[structured programming][] language, but clox bytecode isn't. The right -- or
wrong, depending on how you look at it -- set of bytecode instructions could
jump into the middle of a block, or from one scope into another.
-->
编译成字节码时，代码里显式的嵌套块结构蒸发了，只剩下一串扁平的指令。Lox 是一门[结构化编程][structured programming]语言，但 clox 字节码不是。一组“正确”——或“错误”，看你怎么看——的字节码指令，可以跳进块的中间，或从一个作用域跳进另一个。

<!--
The VM will happily execute that, even if the result leaves the stack in an
unknown, inconsistent state. So even though the bytecode is unstructured, we'll
take care to ensure that our compiler only generates clean code that maintains
the same structure and nesting that Lox itself does.
-->
虚拟机会乐呵呵地执行那一切，即便结果让栈处于未知、不一致的状态。所以，即便字节码是非结构化的，我们也要小心确保编译器只生成干净的代码，维持与 Lox 本身相同的结构与嵌套。

<!--
This is exactly how real CPUs behave. Even though we might program them using
higher-level languages that mandate structured control flow, the compiler lowers
that down to raw jumps. At the bottom, it turns out goto is the only real
control flow.
-->
真正的 CPU 正是如此行事。即便我们用强制结构化控制流的高级语言来写，编译器也会把它降到原始跳转。到了最底层，原来 goto 才是唯一真正的控制流。

[structured programming]: https://en.wikipedia.org/wiki/Structured_programming

<!--
Anyway, I didn't mean to get all philosophical. The important bit is that if we
have that one conditional jump instruction, that's enough to implement Lox's
`if` statement, as long as it doesn't have an `else` clause. So let's go ahead
and get started with that.
-->
总之，我本无意扯那么哲学。要紧的是：只要有那一条条件跳转指令，就足以实现没有 `else` 子句的 Lox `if` 语句。那咱们就动手吧。

<!--
-- If Statements
-->
## if 语句

<!--
This many chapters in, you know the drill. Any new feature starts in the front
end and works its way through the pipeline. An `if` statement is, well, a
statement, so that's where we hook it into the parser.
-->
写到这么多章了，你知道套路。任何新特性从前端起步，一路穿过流水线。`if` 语句嘛，就是一条语句，所以我们在解析器里从这儿挂上。

^code parse-if (2 before, 1 after)

<!--
When we see an `if` keyword, we hand off compilation to this function:
-->
看见 `if` 关键字时，我们把编译交给这个函数：

^code if-statement

<aside name="paren">

<!--
Have you ever noticed that the `(` after the `if` keyword doesn't actually do
anything useful? The language would be just as unambiguous and easy to parse
without it, like:
-->
你有没有注意到：`if` 关键字后面的 `(` 其实并不干任何有用的事？没有它，语言同样无歧义、同样好解析，比如：

```lox
if condition) print("looks weird");
```

<!--
The closing `)` is useful because it separates the condition expression from the
body. Some languages use a `then` keyword instead. But the opening `(` doesn't
do anything. It's just there because unmatched parentheses look bad to us
humans.
-->
收尾的 `)` 有用，因为它把条件表达式与语句体隔开。有些语言改用 `then` 关键字。但开头的 `(` 什么也不做——它在那儿，只因为不成对的括号在我们人类眼里难看。

</aside>

<!--
First we compile the condition expression, bracketed by parentheses. At runtime,
that will leave the condition value on top of the stack. We'll use that to
determine whether to execute the then branch or skip it.
-->
首先，我们编译括在圆括号里的条件表达式。运行时，那会把条件值留在栈顶。我们靠它决定是执行 then 分支还是跳过。

<!--
Then we emit a new `OP_JUMP_IF_FALSE` instruction. It has an operand for how
much to offset the `ip` -- how many bytes of code to skip. If the condition is
falsey, it adjusts the `ip` by that amount. Something like this:
-->
然后我们发出一条新的 `OP_JUMP_IF_FALSE` 指令。它有一个操作数，表示要把 `ip` 偏移多少——跳过多少字节的代码。若条件为假值，就按该量调整 `ip`。大致像这样：

<aside name="legend">

<!--
The boxes with the torn edges here represent the blob of bytecode generated by
compiling some sub-clause of a control flow construct. So the "condition
expression" box is all of the instructions emitted when we compiled that
expression.
-->
这里带撕边的方框，代表编译控制流构造某个子句时生成的那坨字节码。所以“条件表达式”框，就是编译该表达式时发出的全部指令。

</aside>

<span name="legend"></span>

<img src="image/jumping-back-and-forth/if-without-else.png" alt="Flowchart of the compiled bytecode of an if statement." />

<!--
But we have a problem. When we're writing the `OP_JUMP_IF_FALSE` instruction's
operand, how do we know how far to jump? We haven't compiled the then branch
yet, so we don't know how much bytecode it contains.
-->
可我们有个问题。写 `OP_JUMP_IF_FALSE` 指令的操作数时，怎么知道要跳多远？then 分支还没编译，我们不知道它包含多少字节码。

<!--
To fix that, we use a classic trick called **backpatching**. We emit the jump
instruction first with a placeholder offset operand. We keep track of where that
half-finished instruction is. Next, we compile the then body. Once that's done,
we know how far to jump. So we go back and replace that placeholder offset with
the real one now that we can calculate it. Sort of like sewing a patch onto the
existing fabric of the compiled code.
-->
为解决这点，我们用一个经典招数，叫做**回填**（backpatching）。先发出带占位偏移操作数的跳转指令，记下那条半成品指令的位置。接着编译 then 体。一旦做完，就知道要跳多远了。于是我们回头，用现在能算出的真实偏移替换那个占位符——有点像在已编译代码的布料上缝上一块补丁。

<img src="image/jumping-back-and-forth/patch.png" alt="A patch containing a number being sewn onto a sheet of bytecode." />

<!--
We encode this trick into two helper functions.
-->
我们把这招编进两个辅助函数。

^code emit-jump

<!--
The first emits a bytecode instruction and writes a placeholder operand for the
jump offset. We pass in the opcode as an argument because later we'll have two
different instructions that use this helper. We use two bytes for the jump
offset operand. A 16-bit <span name="offset">offset</span> lets us jump over up
to 65,536 bytes of code, which should be plenty for our needs.
-->
第一个发出一条字节码指令，并为跳转偏移写上占位操作数。我们把操作码当参数传入，因为稍后会有两条不同指令共用这个助手。跳转偏移操作数用两个字节。16 位<span name="offset">偏移</span>最多能跳过 65,536 字节的代码，对我们来说应当绰绰有余。

<aside name="offset">

<!--
Some instruction sets have separate "long" jump instructions that take larger
operands for when you need to jump a greater distance.
-->
有些指令集另有“长”跳转指令，在需要跳得更远时使用更大的操作数。

</aside>

<!--
The function returns the offset of the emitted instruction in the chunk. After
compiling the then branch, we take that offset and pass it to this:
-->
该函数返回已发出指令在块中的偏移。编译完 then 分支后，我们拿这个偏移传给下面这个：

^code patch-jump

<!--
This goes back into the bytecode and replaces the operand at the given location
with the calculated jump offset. We call `patchJump()` right before we emit the
next instruction that we want the jump to land on, so it uses the current
bytecode count to determine how far to jump. In the case of an `if` statement,
that means right after we compile the then branch and before we compile the next
statement.
-->
它回到字节码里，用算出的跳转偏移替换给定位置的操作数。我们在发出“希望跳转落点”的下一条指令之前调用 `patchJump()`，这样它用当前字节码计数来确定跳多远。对 `if` 语句来说，就是刚编译完 then 分支、编译下一条语句之前。

<!--
That's all we need at compile time. Let's define the new instruction.
-->
编译期需要的就这些。来定义新指令。

^code jump-if-false-op (1 before, 1 after)

<!--
Over in the VM, we get it working like so:
-->
到虚拟机那边，我们这样让它工作：

^code op-jump-if-false (2 before, 1 after)

<!--
This is the first instruction we've added that takes a 16-bit operand. To read
that from the chunk, we use a new macro.
-->
这是我们加入的第一条带 16 位操作数的指令。要从块里读它，我们用一个新宏。

^code read-short (1 before, 1 after)

<!--
It yanks the next two bytes from the chunk and builds a 16-bit unsigned integer
out of them. As usual, we clean up our macro when we're done with it.
-->
它从块里拽出接下来两个字节，拼成一个 16 位无符号整数。照例，用完后我们清理这个宏。

^code undef-read-short (1 before, 1 after)

<!--
After reading the offset, we check the condition value on top of the stack.
<span name="if">If</span> it's falsey, we apply this jump offset to the `ip`.
Otherwise, we leave the `ip` alone and execution will automatically proceed to
the next instruction following the jump instruction.
-->
读完偏移后，我们检查栈顶的条件值。<span name="if">若</span>为假值，就把这个跳转偏移施加到 `ip` 上。否则不动 `ip`，执行会自动落到跳转指令后面的下一条指令。

<!--
In the case where the condition is falsey, we don't need to do any other work.
We've offset the `ip`, so when the outer instruction dispatch loop turns again,
it will pick up execution at that new instruction, past all of the code in the
then branch.
-->
条件为假值时，我们不必再做别的。我们已经偏移了 `ip`，外层指令分派循环再转一圈时，就会从那条新指令接着执行——已经越过 then 分支里的全部代码。

<aside name="if">

<!--
I said we wouldn't use C's `if` statement to implement Lox's control flow, but
we do use one here to determine whether or not to offset the instruction
pointer. But we aren't really using C for *control flow*. If we wanted to, we
could do the same thing purely arithmetically. Let's assume we have a function
`falsey()` that takes a Lox Value and returns 1 if it's falsey or 0 otherwise.
Then we could implement the jump instruction like:
-->
我说过不会用 C 的 `if` 来实现 Lox 的控制流，可这里确实用了一条，来决定是否偏移指令指针。但我们并不是真在用 C 做*控制流*。若愿意，可以纯用算术做同样的事。假设有个函数 `falsey()`，吃一个 Lox 值，假值返回 1，否则返回 0。那跳转指令可以这样实现：

```c
case OP_JUMP_IF_FALSE: {
  uint16_t offset = READ_SHORT();
  vm.ip += falsey() * offset;
  break;
}
```

<!--
The `falsey()` function would probably use some control flow to handle the
different value types, but that's an implementation detail of that function and
doesn't affect how our VM does its own control flow.
-->
`falsey()` 函数大概会用一点控制流来处理不同值类型，但那是该函数的实现细节，并不影响我们的虚拟机如何做自己的控制流。

</aside>

<!--
Note that the jump instruction doesn't pop the condition value off the stack. So
we aren't totally done here, since this leaves an extra value floating around on
the stack. We'll clean that up soon. Ignoring that for the moment, we do have a
working `if` statement in Lox now, with only one little instruction required to
support it at runtime in the VM.
-->
注意：跳转指令并不会把条件值从栈上弹出。所以我们还没完全做完——栈上多漂着一个值。很快会清掉。眼下先忽略这点，我们在 Lox 里已经有了能工作的 `if` 语句，运行时虚拟机只需一条小小的指令来支持它。

<!--
-- Else clauses
-->
### else 子句

<!--
An `if` statement without support for `else` clauses is like Morticia Addams
without Gomez. So, after we compile the then branch, we look for an `else`
keyword. If we find one, we compile the else branch.
-->
没有 `else` 子句的 `if`，就像没有 Gomez 的 Morticia Addams。所以，编译完 then 分支后，我们找有没有 `else` 关键字。找到了，就编译 else 分支。

^code compile-else (1 before, 1 after)

<!--
When the condition is falsey, we'll jump over the then branch. If there's an
else branch, the `ip` will land right at the beginning of its code. But that's
not enough, though. Here's the flow that leads to:
-->
条件为假值时，我们会跳过 then 分支。若有 else 分支，`ip` 会正好落在其代码开头。但这还不够。那样会得到这样的流：

<img src="image/jumping-back-and-forth/bad-else.png" alt="Flowchart of the compiled bytecode with the then branch incorrectly falling through to the else branch." />

<!--
If the condition is truthy, we execute the then branch like we want. But after
that, execution rolls right on through into the else branch. Oops! When the
condition is true, after we run the then branch, we need to jump over the else
branch. That way, in either case, we only execute a single branch, like this:
-->
条件为真值时，我们会按期望执行 then 分支。可之后执行会径直滚进 else 分支。糟糕！条件为真时，跑完 then 分支后，我们还得跳过 else 分支。这样无论哪种情况，都只执行一个分支，像这样：

<img src="image/jumping-back-and-forth/if-else.png" alt="Flowchart of the compiled bytecode for an if with an else clause." />

<!--
To implement that, we need another jump from the end of the then branch.
-->
要实现这点，我们需要从 then 分支末尾再来一次跳转。

^code jump-over-else (2 before, 1 after)

<!--
We patch that offset after the end of the else body.
-->
在 else 体结束之后，我们修补那个偏移。

^code patch-else (1 before, 1 after)

<!--
After executing the then branch, this jumps to the next statement after the else
branch. Unlike the other jump, this jump is unconditional. We always take it, so
we need another instruction that expresses that.
-->
执行完 then 分支后，这会跳到 else 分支之后的下一条语句。与另一条跳转不同，这次是无条件的——我们总会走它，所以需要另一条指令来表达这点。

^code jump-op (1 before, 1 after)

<!--
We interpret it like so:
-->
解释起来是这样：

^code op-jump (2 before, 1 after)

<!--
Nothing too surprising here -- the only difference is that it doesn't check a
condition and always applies the offset.
-->
没什么太意外的——唯一差别是它不检查条件，总是施加偏移。

<!--
We have then and else branches working now, so we're close. The last bit is to
clean up that condition value we left on the stack. Remember, each statement is
required to have zero stack effect -- after the statement is finished executing,
the stack should be as tall as it was before.
-->
then 与 else 分支现在都能工作了，就差最后一点：清掉我们留在栈上的那个条件值。记住，每条语句的栈效应必须为零——语句执行完毕后，栈的高度应与之前一样。

<!--
We could have the `OP_JUMP_IF_FALSE` instruction pop the condition itself, but
soon we'll use that same instruction for the logical operators where we don't
want the condition popped. Instead, we'll have the compiler emit a couple of
explicit `OP_POP` instructions when compiling an `if` statement. We need to take
care that every execution path through the generated code pops the condition.
-->
本可以让 `OP_JUMP_IF_FALSE` 自己弹出条件，但很快我们会把同一条指令用于逻辑运算符，那时并不想弹出条件。于是改由编译器在编译 `if` 时发出几条显式的 `OP_POP`。我们要留心：穿过生成代码的每条执行路径都弹出条件。

<!--
When the condition is truthy, we pop it right before the code inside the then
branch.
-->
条件为真值时，我们在 then 分支内部代码之前立刻弹出它。

^code pop-then (1 before, 1 after)

<!--
Otherwise, we pop it at the beginning of the else branch.
-->
否则，在 else 分支开头弹出。

^code pop-end (1 before, 2 after)

<!--
This little instruction here also means that every `if` statement has an
implicit else branch even if the user didn't write an `else` clause. In the case
where they left it off, all the branch does is discard the condition value.
-->
这儿这条小指令还意味着：即便用户没写 `else` 子句，每条 `if` 也有一个隐式的 else 分支。省略时，该分支只做一件事——丢掉条件值。

<!--
The full correct flow looks like this:
-->
完整正确的流长这样：

<img src="image/jumping-back-and-forth/full-if-else.png" alt="Flowchart of the compiled bytecode including necessary pop instructions." />

<!--
If you trace through, you can see that it always executes a single branch and
ensures the condition is popped first. All that remains is a little disassembler
support.
-->
若你跟着走一遍，会看见它总是只执行一个分支，并确保先弹出条件。剩下的只是一点点反汇编器支持。

^code disassemble-jump (1 before, 1 after)

<!--
These two instructions have a new format with a 16-bit operand, so we add a new
utility function to disassemble them.
-->
这两条指令有带 16 位操作数的新格式，所以我们加一个新工具函数来反汇编它们。

^code jump-instruction

<!--
There we go, that's one complete control flow construct. If this were an '80s
movie, the montage music would kick in and the rest of the control flow syntax
would take care of itself. Alas, the <span name="80s">'80s</span> are long over,
so we'll have to grind it out ourselves.
-->
好了，这就是一个完整的控制流构造。若这是部八十年代电影，蒙太奇音乐该响起来，其余控制流语法会自己搞定。可惜<span name="80s">八十年代</span>早结束了，我们得自己硬啃。

<aside name="80s">

<!--
My enduring love of Depeche Mode notwithstanding.
-->
尽管我对 Depeche Mode 的爱经久不衰。

</aside>

<!--
-- Logical Operators
-->
## 逻辑运算符

<!--
You probably remember this from jlox, but the logical operators `and` and `or`
aren't just another pair of binary operators like `+` and `-`. Because they
short-circuit and may not evaluate their right operand depending on the value of
the left one, they work more like control flow expressions.
-->
你大概还记得 jlox 里的事：逻辑运算符 `and` 与 `or` 并不只是像 `+` 和 `-` 那样的另一对二元运算符。因为它们会短路——视左操作数的值而定，可能根本不求值右操作数——所以它们更像控制流表达式。

<!--
They're basically a little variation on an `if` statement with an `else` clause.
The easiest way to explain them is to just show you the compiler code and the
control flow it produces in the resulting bytecode. Starting with `and`, we hook
it into the expression parsing table here:
-->
它们基本上是带 `else` 子句的 `if` 语句的小小变体。最省事的解释方式，就是直接给你看编译器代码，以及它在结果字节码里产生的控制流。从 `and` 开始，我们在表达式解析表里挂上：

^code table-and (1 before, 1 after)

<!--
That hands off to a new parser function.
-->
那会交给一个新的解析函数。

^code and

<!--
At the point this is called, the left-hand side expression has already been
compiled. That means at runtime, its value will be on top of the stack. If that
value is falsey, then we know the entire `and` must be false, so we skip the
right operand and leave the left-hand side value as the result of the entire
expression. Otherwise, we discard the left-hand value and evaluate the right
operand which becomes the result of the whole `and` expression.
-->
调用到这儿时，左手表达式已经编译完了。这意味着运行时其值会在栈顶。若该值为假值，整条 `and` 必为假，于是我们跳过右操作数，把左手值留作整个表达式的结果。否则，丢掉左手值，求值右操作数，它就成为整个 `and` 表达式的结果。

<!--
Those four lines of code right there produce exactly that. The flow looks like
this:
-->
就那四行代码，正好产生上述效果。流长这样：

<img src="image/jumping-back-and-forth/and.png" alt="Flowchart of the compiled bytecode of an 'and' expression." />

<!--
Now you can see why `OP_JUMP_IF_FALSE` <span name="instr">leaves</span> the
value on top of the stack. When the left-hand side of the `and` is falsey, that
value sticks around to become the result of the entire expression.
-->
现在你能明白，为何 `OP_JUMP_IF_FALSE` 会把值<span name="instr">留在</span>栈顶。当 `and` 的左手为假值时，那个值会留下来，成为整个表达式的结果。

<aside name="instr">

<!--
We've got plenty of space left in our opcode range, so we could have separate
instructions for conditional jumps that implicitly pop and those that don't, I
suppose. But I'm trying to keep things minimal for the book. In your bytecode
VM, it's worth exploring adding more specialized instructions and seeing how
they affect performance.
-->
操作码空间还剩不少，本可以分别为“隐式弹出”与“不弹出”的条件跳转设不同指令，我想。但为了本书，我尽量保持精简。在你自己的字节码虚拟机里，值得探索加更多特化指令，看看它们如何影响性能。

</aside>

<!--
-- Logical or operator
-->
### 逻辑 or 运算符

<!--
The `or` operator is a little more complex. First we add it to the parse table.
-->
`or` 运算符稍微复杂些。先把它加进解析表。

^code table-or (1 before, 1 after)

<!--
When that parser consumes an infix `or` token, it calls this:
-->
解析器消费到中缀 `or` 记号时，会调用这个：

^code or

<!--
In an `or` expression, if the left-hand side is *truthy*, then we skip over the
right operand. Thus we need to jump when a value is truthy. We could add a
separate instruction, but just to show how our compiler is free to map the
language's semantics to whatever instruction sequence it wants, I implemented it
in terms of the jump instructions we already have.
-->
在 `or` 表达式里，若左手是*真值*，我们就跳过右操作数。于是需要在值为真时跳转。本可以另加一条指令，但为了展示编译器可以自由地把语言语义映射成任意指令序列，我用已有的跳转指令来实现它。

<!--
When the left-hand side is falsey, it does a tiny jump over the next statement.
That statement is an unconditional jump over the code for the right operand.
This little dance effectively does a jump when the value is truthy. The flow
looks like this:
-->
左手为假值时，它做一个小小的跳转，越过下一条语句。那条语句是无条件跳过右操作数代码。这套小舞步，实际上就在值为真时完成了跳转。流长这样：

<img src="image/jumping-back-and-forth/or.png" alt="Flowchart of the compiled bytecode of a logical or expression." />

<!--
If I'm honest with you, this isn't the best way to do this. There are more
instructions to dispatch and more overhead. There's no good reason why `or`
should be slower than `and`. But it is kind of fun to see that it's possible to
implement both operators without adding any new instructions. Forgive me my
indulgences.
-->
实话说，这不是最好的做法。要分派的指令更多，开销也更大。没有正当理由让 `or` 比 `and` 更慢。但看见不增加任何新指令也能实现两个运算符，还是挺好玩的。请原谅我的放纵。

<!--
OK, those are the three *branching* constructs in Lox. By that, I mean, these
are the control flow features that only jump *forward* over code. Other
languages often have some kind of multi-way branching statement like `switch`
and maybe a conditional expression like `?:`, but Lox keeps it simple.
-->
好了，这就是 Lox 里三种*分支*构造。我的意思是：这些控制流特性只*向前*跳过代码。其他语言常有某种多路分支语句，比如 `switch`，或许还有像 `?:` 这样的条件表达式，但 Lox 保持简单。

<!--
-- While Statements
-->
## while 语句

<!--
That takes us to the *looping* statements, which jump *backward* so that code
can be executed more than once. Lox only has two loop constructs, `while` and
`for`. A `while` loop is (much) simpler, so we start the party there.
-->
接下来是*循环*语句——它们*向后*跳转，好让代码能执行不止一次。Lox 只有两种循环构造：`while` 与 `for`。`while` 循环（远）更简单，我们就从这儿开场。

^code parse-while (1 before, 1 after)

<!--
When we reach a `while` token, we call:
-->
遇到 `while` 记号时，我们调用：

^code while-statement

<!--
Most of this mirrors `if` statements -- we compile the condition expression,
surrounded by mandatory parentheses. That's followed by a jump instruction that
skips over the subsequent body statement if the condition is falsey.
-->
大部分与 `if` 语句镜像——我们编译强制用括号围住的条件表达式。随后是一条跳转指令：条件为假值时，跳过后面的体语句。

<!--
We patch the jump after compiling the body and take care to <span
name="pop">pop</span> the condition value from the stack on either path. The
only difference from an `if` statement is the loop. That looks like this:
-->
编译完体之后修补跳转，并留心在两条路径上都从栈上<span
name="pop">弹出</span>条件值。与 `if` 语句唯一的差别是循环。那长这样：

<aside name="pop">

<!--
Really starting to second-guess my decision to use the same jump instructions
for the logical operators.
-->
真开始后悔用同一套跳转指令来伺候逻辑运算符了。

</aside>

^code loop (1 before, 2 after)

<!--
After the body, we call this function to emit a "loop" instruction. That
instruction needs to know how far back to jump. When jumping forward, we had to
emit the instruction in two stages since we didn't know how far we were going to
jump until after we emitted the jump instruction. We don't have that problem
now. We've already compiled the point in code that we want to jump back to --
it's right before the condition expression.
-->
体之后，我们调用这个函数发出一条“循环”指令。该指令需要知道向后跳多远。向前跳时，我们得分两阶段发出指令，因为发出跳转指令时还不知道要跳多远。现在没有那个问题。我们想跳回的那个代码点已经编译过了——就在条件表达式正前方。

<!--
All we need to do is capture that location as we compile it.
-->
我们只需在编译时捕获那个位置。

^code loop-start (1 before, 1 after)

<!--
After executing the body of a `while` loop, we jump all the way back to before
the condition. That way, we re-evaluate the condition expression on each
iteration. We store the chunk's current instruction count in `loopStart` to
record the offset in the bytecode right before the condition expression we're
about to compile. Then we pass that into this helper function:
-->
执行完 `while` 循环体后，我们一路跳回条件之前。这样，每次迭代都会重新求值条件表达式。我们把块当前的指令计数存进 `loopStart`，记下即将编译的条件表达式正前方在字节码里的偏移。然后把它传给这个辅助函数：

^code emit-loop

<!--
It's a bit like `emitJump()` and `patchJump()` combined. It emits a new loop
instruction, which unconditionally jumps *backwards* by a given offset. Like the
jump instructions, after that we have a 16-bit operand. We calculate the offset
from the instruction we're currently at to the `loopStart` point that we want to
jump back to. The `+ 2` is to take into account the size of the `OP_LOOP`
instruction's own operands which we also need to jump over.
-->
它有点像 `emitJump()` 与 `patchJump()` 的合体。发出一条新的循环指令，无条件地按给定偏移*向后*跳。与跳转指令一样，后面跟 16 位操作数。我们从当前所在指令算到想跳回的 `loopStart` 点。`+ 2` 是为了把 `OP_LOOP` 指令自身操作数的大小也算进去——那些我们也得跳过。

<!--
From the VM's perspective, there really is no semantic difference between
`OP_LOOP` and `OP_JUMP`. Both just add an offset to the `ip`. We could have used
a single instruction for both and given it a signed offset operand. But I
figured it was a little easier to sidestep the annoying bit twiddling required
to manually pack a signed 16-bit integer into two bytes, and we've got the
opcode space available, so why not use it?
-->
从虚拟机的角度看，`OP_LOOP` 与 `OP_JUMP` 其实没有语义差别。两者都只是给 `ip` 加一个偏移。本可以用一条指令伺候两者，给它带符号的偏移操作数。可我觉得，避开把有符号 16 位整数手动塞进两个字节那种烦人的位操作会轻松一点；况且操作码空间有余，何不拿来用？

<!--
The new instruction is here:
-->
新指令在这儿：

^code loop-op (1 before, 1 after)

<!--
And in the VM, we implement it thusly:
-->
在虚拟机里，我们这样实现：

^code op-loop (1 before, 1 after)

<!--
The only difference from `OP_JUMP` is a subtraction instead of an addition.
Disassembly is similar too.
-->
与 `OP_JUMP` 唯一的差别是减法而非加法。反汇编也类似。

^code disassemble-loop (1 before, 1 after)

<!--
That's our `while` statement. It contains two jumps -- a conditional forward one
to escape the loop when the condition is not met, and an unconditional loop
backward after we have executed the body. The flow looks like this:
-->
这就是我们的 `while` 语句。它包含两次跳转——一次有条件向前，条件不满足时逃出循环；一次无条件向后循环，在执行完体之后。流长这样：

<img src="image/jumping-back-and-forth/while.png" alt="Flowchart of the compiled bytecode of a while statement." />

<!--
-- For Statements
-->
## for 语句

<!--
The other looping statement in Lox is the venerable `for` loop, inherited from
C. It's got a lot more going on with it compared to a `while` loop. It has three
clauses, all of which are optional:
-->
Lox 里另一种循环语句，是从 C 继承来的古老 `for` 循环。与 `while` 相比，它花样多得多。它有三个子句，全都可选：

<span name="detail"></span>

<!--
*   The initializer can be a variable declaration or an expression. It runs once
    at the beginning of the statement.

*   The condition clause is an expression. Like in a `while` loop, we exit the
    loop when it evaluates to something falsey.

*   The increment expression runs once at the end of each loop iteration.
-->
*   初始化子句可以是变量声明或表达式。它在语句开头只跑一次。

*   条件子句是一个表达式。像 `while` 循环一样，求值为假值时退出循环。

*   递增表达式在每次循环迭代末尾跑一次。

<aside name="detail">

<!--
If you want a refresher, the corresponding chapter in part II goes through the
semantics [in more detail][jlox].
-->
若想温习，第二部分对应章节会[更详细地][jlox]讲语义。

[jlox]: control-flow.html#for-loops

</aside>

<!--
In jlox, the parser desugared a `for` loop to a synthesized AST for a `while`
loop with some extra stuff before it and at the end of the body. We'll do
something similar, though we won't go through anything like an AST. Instead,
our bytecode compiler will use the jump and loop instructions we already have.
-->
在 jlox 里，解析器把 `for` 循环脱糖成一个合成的 `while` 循环 AST，前后再加点东西。我们会做类似的事，只是不会经过任何像 AST 的东西。取而代之，字节码编译器会用我们已经有的跳转与循环指令。

<!--
We'll work our way through the implementation a piece at a time, starting with
the `for` keyword.
-->
我们一块一块推进实现，从 `for` 关键字开始。

^code parse-for (1 before, 1 after)

<!--
It calls a helper function. If we only supported `for` loops with empty clauses
like `for (;;)`, then we could implement it like this:
-->
它调用一个辅助函数。若我们只支持像 `for (;;)` 这种空子句的 `for` 循环，可以这样实现：

^code for-statement

<!--
There's a bunch of mandatory punctuation at the top. Then we compile the body.
Like we did for `while` loops, we record the bytecode offset at the top of the
body and emit a loop to jump back to that point after it. We've got a working
implementation of <span name="infinite">infinite</span> loops now.
-->
顶部有一堆强制标点。然后我们编译体。像 `while` 循环那样，在体顶部记录字节码偏移，并在体后发出一条循环跳回该点。现在我们有了一个能工作的<span name="infinite">无限</span>循环实现。

<aside name="infinite">

<!--
Alas, without `return` statements, there isn't any way to terminate it short of
a runtime error.
-->
唉，没有 `return` 语句的话，除了运行时错误，没有别的办法终止它。

</aside>

<!--
-- Initializer clause
-->
### 初始化子句

<!--
Now we'll add the first clause, the initializer. It executes only once, before
the body, so compiling is straightforward.
-->
现在加上第一个子句：初始化。它在体之前只执行一次，所以编译很直接。

^code for-initializer (1 before, 2 after)

<!--
The syntax is a little complex since we allow either a variable declaration or
an expression. We use the presence of the `var` keyword to tell which we have.
For the expression case, we call `expressionStatement()` instead of
`expression()`. That looks for a semicolon, which we need here too, and also
emits an `OP_POP` instruction to discard the value. We don't want the
initializer to leave anything on the stack.
-->
语法稍复杂，因为我们既允许变量声明，也允许表达式。用有没有 `var` 关键字来区分。表达式情形下，我们调用 `expressionStatement()` 而不是 `expression()`。它会找分号——这儿也需要——并发出 `OP_POP` 丢掉值。我们不想让初始化子句在栈上留下任何东西。

<!--
If a `for` statement declares a variable, that variable should be scoped to the
loop body. We ensure that by wrapping the whole statement in a scope.
-->
若 `for` 语句声明了变量，该变量的作用域应限于循环体。我们把整个语句包进一个作用域来确保这点。

^code for-begin-scope (1 before, 1 after)

<!--
Then we close it at the end.
-->
然后在末尾关闭它。

^code for-end-scope (1 before, 1 after)

<!--
-- Condition clause
-->
### 条件子句

<!--
Next, is the condition expression that can be used to exit the loop.
-->
接下来是可用于退出循环的条件表达式。

^code for-exit (1 before, 1 after)

<!--
Since the clause is optional, we need to see if it's actually present. If the
clause is omitted, the next token must be a semicolon, so we look for that to
tell. If there isn't a semicolon, there must be a condition expression.
-->
子句可选，所以我们要看它是否真的存在。若省略，下一个记号必是分号，我们就靠这个判断。若没有分号，就一定有条件表达式。

<!--
In that case, we compile it. Then, just like with while, we emit a conditional
jump that exits the loop if the condition is falsey. Since the jump leaves the
value on the stack, we pop it before executing the body. That ensures we discard
the value when the condition is true.
-->
那种情况下，我们编译它。然后，就像 while 一样，发出一条条件跳转：条件为假值时退出循环。由于跳转会把值留在栈上，我们在执行体之前弹出它。这确保条件为真时丢掉该值。

<!--
After the loop body, we need to patch that jump.
-->
循环体之后，我们需要修补那次跳转。

^code exit-jump (1 before, 2 after)

<!--
We do this only when there is a condition clause. If there isn't, there's no
jump to patch and no condition value on the stack to pop.
-->
仅在有条件子句时才做这些。若没有，就没有跳转可修补，栈上也没有条件值可弹。

<!--
-- Increment clause
-->
### 递增子句

<!--
I've saved the best for last, the increment clause. It's pretty convoluted. It
appears textually before the body, but executes *after* it. If we parsed to an
AST and generated code in a separate pass, we could simply traverse into and
compile the `for` statement AST's body field before its increment clause.
-->
压轴的是最好的：递增子句。它相当绕。文本上它出现在体之前，却在体*之后*执行。若我们解析成 AST，再在单独一遍里生成代码，可以先遍历并编译 `for` 语句 AST 的体字段，再编译递增子句。

<!--
Unfortunately, we can't compile the increment clause later, since our compiler
only makes a single pass over the code. Instead, we'll *jump over* the
increment, run the body, jump *back* up to the increment, run it, and then go to
the next iteration.
-->
可惜我们不能稍后才编译递增子句，因为编译器只对代码走单遍。于是我们改为*跳过*递增、跑体、再*跳回*递增、跑它，然后进入下一次迭代。

<!--
I know, a little weird, but hey, it beats manually managing ASTs in memory in C,
right? Here's the code:
-->
我知道，有点怪，可嘿，总好过在 C 里手动管理内存中的 AST，对吧？代码在这儿：

^code for-increment (2 before, 2 after)

<!--
Again, it's optional. Since this is the last clause, when omitted, the next
token will be the closing parenthesis. When an increment is present, we need to
compile it now, but it shouldn't execute yet. So, first, we emit an
unconditional jump that hops over the increment clause's code to the body of the
loop.
-->
同样是可选的。这是最后一个子句，省略时下一个记号会是右括号。有递增时，我们现在就得编译它，但还不该执行。所以先发出一条无条件跳转，越过递增子句的代码，落到循环体。

<!--
Next, we compile the increment expression itself. This is usually an assignment.
Whatever it is, we only execute it for its side effect, so we also emit a pop to
discard its value.
-->
接着，编译递增表达式本身。通常是一次赋值。不管怎样，我们只为副作用执行它，所以再发出一条 pop 丢掉其值。

<!--
The last part is a little tricky. First, we emit a loop instruction. This is the
main loop that takes us back to the top of the `for` loop -- right before the
condition expression if there is one. That loop happens right after the
increment, since the increment executes at the end of each loop iteration.
-->
最后一部分有点刁。首先发出一条循环指令。这是把我们带回 `for` 循环顶部的主循环——若有条件表达式，就回到它正前方。该循环紧跟在递增之后，因为递增在每次循环迭代末尾执行。

<!--
Then we change `loopStart` to point to the offset where the increment expression
begins. Later, when we emit the loop instruction after the body statement, this
will cause it to jump up to the *increment* expression instead of the top of the
loop like it does when there is no increment. This is how we weave the
increment in to run after the body.
-->
然后我们改 `loopStart`，指向递增表达式开始处的偏移。稍后，在体语句之后发出循环指令时，这会让它跳上到*递增*表达式，而不是像没有递增时那样跳到循环顶部。我们就是这样把递增织进体之后再跑。

<!--
It's convoluted, but it all works out. A complete loop with all the clauses
compiles to a flow like this:
-->
很绕，但都能跑通。带齐全部子句的完整循环，会编译成这样的流：

<img src="image/jumping-back-and-forth/for.png" alt="Flowchart of the compiled bytecode of a for statement." />

<!--
As with implementing `for` loops in jlox, we didn't need to touch the runtime.
It all gets compiled down to primitive control flow operations the VM already
supports. In this chapter, we've taken a big <span name="leap">leap</span>
forward -- clox is now Turing complete. We've also covered quite a bit of new
syntax: three statements and two expression forms. Even so, it only took three
new simple instructions. That's a pretty good effort-to-reward ratio for the
architecture of our VM.
-->
与在 jlox 里实现 `for` 循环一样，我们不必碰运行时。一切都编译成虚拟机已支持的原始控制流操作。本章我们迈出了一大<span name="leap">步</span>——clox 现在图灵完备了。我们也覆盖了不少新语法：三条语句、两种表达式形式。即便如此，只用了三条新的简单指令。对我们虚拟机架构来说，投入产出比相当不错。

<aside name="leap">

<!--
I couldn't resist the pun. I regret nothing.
-->
我忍不住玩了个双关。毫无悔意。

</aside>

<div class="challenges">

<!--
-- Challenges
-->
## 挑战

<!--
1.  In addition to `if` statements, most C-family languages have a multi-way
    `switch` statement. Add one to clox. The grammar is:
-->
1.  除了 `if` 语句，多数 C 族语言还有多路 `switch` 语句。给 clox 加一个。语法是：

    ```ebnf
    switchStmt     → "switch" "(" expression ")"
                     "{" switchCase* defaultCase? "}" ;
    switchCase     → "case" expression ":" statement* ;
    defaultCase    → "default" ":" statement* ;
    ```

<!--
    To execute a `switch` statement, first evaluate the parenthesized switch
    value expression. Then walk the cases. For each case, evaluate its value
    expression. If the case value is equal to the switch value, execute the
    statements under the case and then exit the `switch` statement. Otherwise,
    try the next case. If no case matches and there is a `default` clause,
    execute its statements.

    To keep things simpler, we're omitting fallthrough and `break` statements.
    Each case automatically jumps to the end of the switch statement after its
    statements are done.
-->
    执行 `switch` 语句时，先求值括号里的 switch 值表达式。然后遍历各 case。对每个 case，求值其值表达式。若 case 值等于 switch 值，就执行该 case 下的语句，然后退出 `switch`。否则试下一个 case。若无一匹配且有 `default` 子句，就执行其子句中的语句。

    为简单起见，我们省略贯穿与 `break` 语句。每个 case 在语句执行完后，自动跳到 switch 语句末尾。

<!--
1.  In jlox, we had a challenge to add support for `break` statements. This
    time, let's do `continue`:
-->
1.  在 jlox 里，我们有一道挑战是加 `break` 语句支持。这一次，我们来做 `continue`：

    ```ebnf
    continueStmt   → "continue" ";" ;
    ```

<!--
    A `continue` statement jumps directly to the top of the nearest enclosing
    loop, skipping the rest of the loop body. Inside a `for` loop, a `continue`
    jumps to the increment clause, if there is one. It's a compile-time error to
    have a `continue` statement not enclosed in a loop.

    Make sure to think about scope. What should happen to local variables
    declared inside the body of the loop or in blocks nested inside the loop
    when a `continue` is executed?
-->
    `continue` 语句直接跳到最近包围循环的顶部，跳过循环体其余部分。在 `for` 循环内，`continue` 会跳到递增子句（若有）。不在循环内的 `continue` 是编译期错误。

    务必想想作用域。执行 `continue` 时，循环体内、或循环内嵌套块里声明的局部变量该怎样？

<!--
1.  Control flow constructs have been mostly unchanged since Algol 68. Language
    evolution since then has focused on making code more declarative and high
    level, so imperative control flow hasn't gotten much attention.

    For fun, try to invent a useful novel control flow feature for Lox. It can
    be a refinement of an existing form or something entirely new. In practice,
    it's hard to come up with something useful enough at this low expressiveness
    level to outweigh the cost of forcing a user to learn an unfamiliar notation
    and behavior, but it's a good chance to practice your design skills.
-->
1.  自 Algol 68 以来，控制流构造大体未变。此后语言演进更关注让代码更声明式、更高级，所以命令式控制流没怎么受关注。

    图个乐子，试着为 Lox 发明一项有用的新颖控制流特性。可以是对现有形式的细化，也可以是全新的东西。实践中，在这个低表达力层面上很难想出足够有用的东西，足以抵消强迫用户学习陌生记法与行为的代价——但这是练习设计功力的好机会。

</div>

<div class="design-note">

<!--
-- Design Note: Considering Goto Harmful
-->
## 设计笔记：再思 Goto 有害论

<!--
Discovering that all of our beautiful structured control flow in Lox is actually
compiled to raw unstructured jumps is like the moment in Scooby Doo when the
monster rips the mask off their face. It was goto all along! Except in this
case, the monster is *under* the mask. We all know goto is evil. But... why?
-->
发现 Lox 里那些美丽的结构化控制流，其实都编译成了原始的非结构化跳转——就像《史酷比》里怪物撕下面具的那一刻。原来一直是 goto！只不过这一次，怪物在面具*底下*。我们都知道 goto 邪恶。可是……为什么？

<!--
It is true that you can write outrageously unmaintainable code using goto. But I
don't think most programmers around today have seen that first hand. It's been a
long time since that style was common. These days, it's a boogie man we invoke
in scary stories around the campfire.
-->
诚然，用 goto 可以写出骇人听闻、难以维护的代码。但我想今天多数程序员并没有亲眼见过。那种风格常见的日子已经很久了。如今它更像篝火边鬼故事里请来的妖怪。

<!--
The reason we rarely confront that monster in person is because Edsger Dijkstra
slayed it with his famous letter "Go To Statement Considered Harmful", published
in *Communications of the ACM* (March, 1968). Debate around structured
programming had been fierce for some time with adherents on both sides, but I
think Dijkstra deserves the most credit for effectively ending it. Most new
languages today have no unstructured jump statements.
-->
我们很少亲自面对那只怪物，是因为 Edsger Dijkstra 用他那封著名的信《Go To Statement Considered Harmful》（发表于 *Communications of the ACM*，1968 年 3 月）把它斩了。围绕结构化编程的辩论曾激烈一时、两边都有拥趸，但我认为 Dijkstra 最有资格被记上一功：他实际上结束了这场辩论。今天多数新语言都没有非结构化跳转语句。

<!--
A one-and-a-half page letter that almost single-handedly destroyed a language
feature must be pretty impressive stuff. If you haven't read it, I encourage you
to do so. It's a seminal piece of computer science lore, one of our tribe's
ancestral songs. Also, it's a nice, short bit of practice for reading academic
CS <span name="style">writing</span>, which is a useful skill to develop.
-->
一封仅一页半、几乎单枪匹马毁掉一项语言特性的信，想必相当厉害。若你还没读过，我鼓励你读一读。它是计算机科学传说里的奠基之作，我们部落的祖歌之一。此外，它也是练习阅读学术 CS<span name="style">写作</span>的一小段好材料——这是值得培养的技能。

<aside name="style">

<!--
That is, if you can get past Dijkstra's insufferable faux-modest
self-aggrandizing writing style:
-->
前提是你能熬过 Dijkstra 那令人难以忍受的假谦虚、自我夸耀文风：

<!--
> More recently I discovered why the use of the go to statement has such
> disastrous effects. ...At that time I did not attach too much importance to
> this discovery; I now submit my considerations for publication because in very
> recent discussions in which the subject turned up, I have been urged to do so.
-->
> 较近些时候，我发现了为何使用 go to 语句会有如此灾难性的效果。……当时我并未太看重这一发现；如今我把这些思考提交发表，是因为在最近几次谈到该主题的讨论中，有人催促我这样做。

<!--
Ah, yet another one of my many discoveries. I couldn't even be bothered to write
it up until the clamoring masses begged me to.
-->
啊，又是我众多发现中的又一个。直到喧嚷的大众恳求，我才肯费心写下来。

</aside>

<!--
I've read it through a number of times, along with a few critiques, responses,
and commentaries. I ended up with mixed feelings, at best. At a very high level,
I'm with him. His general argument is something like this:
-->
我通读过好几遍，也读过一些批评、回应与评注。到头来，充其量是复杂的心情。在很高的层面上，我站他那边。他的总体论证大致是这样：

<!--
1.  As programmers, we write programs -- static text -- but what we care about
    is the actual running program -- its dynamic behavior.

2.  We're better at reasoning about static things than dynamic things. (He
    doesn't provide any evidence to support this claim, but I accept it.)

3.  Thus, the more we can make the dynamic execution of the program reflect its
    textual structure, the better.
-->
1.  作为程序员，我们写的是程序——静态文本——但我们真正关心的是实际运行中的程序——它的动态行为。

2.  我们对静态事物的推理强过对动态事物。（他没提供证据支持这一主张，但我接受。）

3.  因此，越能让程序的动态执行反映其文本结构，越好。

<!--
This is a good start. Drawing our attention to the separation between the code
we write and the code as it runs inside the machine is an interesting insight.
Then he tries to define a "correspondence" between program text and execution.
For someone who spent literally his entire career advocating greater rigor in
programming, his definition is pretty hand-wavey. He says:
-->
这是个好开端。把我们的注意力引向“我们写的代码”与“机器里跑着的代码”之间的分离，是个有趣的洞见。接着他试图定义程序文本与执行之间的“对应”。对一个几乎整个职业生涯都在倡导编程更严格的人来说，他的定义相当含糊其辞。他说：

<!--
> Let us now consider how we can characterize the progress of a process. (You
> may think about this question in a very concrete manner: suppose that a
> process, considered as a time succession of actions, is stopped after an
> arbitrary action, what data do we have to fix in order that we can redo the
> process until the very same point?)
-->
> 现在让我们考虑如何刻画一个过程的进展。（你可以很具体地想这个问题：假设一个过程——被视为动作的时间序列——在任意某个动作之后停下，我们需要固定哪些数据，才能把过程重做到完全同一点？）

<!--
Imagine it like this. You have two computers with the same program running on
the exact same inputs -- so totally deterministic. You pause one of them at an
arbitrary point in its execution. What data would you need to send to the other
computer to be able to stop it exactly as far along as the first one was?
-->
可以这样想象。你有两台电脑，跑同一程序、吃完全相同的输入——因而完全确定。你在执行中任意一点暂停其中一台。要把另一台停在与第一台完全同样远的地方，你需要给它送什么数据？

<!--
If your program allows only simple statements like assignment, it's easy. You
just need to know the point after the last statement you executed. Basically a
breakpoint, the `ip` in our VM, or the line number in an error message. Adding
branching control flow like `if` and `switch` doesn't add any more to this. Even
if the marker points inside a branch, we can still tell where we are.
-->
若程序只允许像赋值这样的简单语句，很容易。你只需知道刚执行完的那条语句之后的位置。基本上就是断点、我们虚拟机里的 `ip`，或错误消息里的行号。加上像 `if` 与 `switch` 这样的分支控制流，并不增加什么。即便标记指向分支内部，我们仍能知道身在何处。

<!--
Once you add function calls, you need something more. You could have paused the
first computer in the middle of a function, but that function may be called from
multiple places. To pause the second machine at exactly the same point in *the
entire program's* execution, you need to pause it on the *right* call to that
function.
-->
一旦加入函数调用，你就需要更多东西。你可能在某个函数中间暂停了第一台电脑，但那个函数可能从多处被调用。要把第二台机器停在*整个程序*执行的完全同一点，你必须把它停在对该函数的*正确那一次*调用上。

<!--
So you need to know not just the current statement, but, for function calls that
haven't returned yet, you need to know the locations of the callsites. In other
words, a call stack, though I don't think that term existed when Dijkstra wrote
this. Groovy.
-->
所以你不仅需要知道当前语句，对尚未返回的函数调用，还需要知道各调用点的位置。换言之，就是调用栈——尽管我想 Dijkstra 写这封信时这个词还不存在。酷。

<!--
He notes that loops make things harder. If you pause in the middle of a loop
body, you don't know how many iterations have run. So he says you also need to
keep an iteration count. And, since loops can nest, you need a stack of those
(presumably interleaved with the call stack pointers since you can be in loops
in outer calls too).
-->
他指出循环会让事情更难。若你在循环体中间暂停，并不知道已跑了多少次迭代。所以他说还需要保留迭代计数。又因为循环可以嵌套，你需要一叠这种计数（想必与调用栈指针交错，因为外层调用里也可能正处于循环中）。

<!--
This is where it gets weird. So we're really building to something now, and you
expect him to explain how goto breaks all of this. Instead, he just says:
-->
这儿开始变得奇怪。我们真的在铺垫什么了，你会期待他解释 goto 如何打破这一切。可他只是说：

<!--
> The unbridled use of the go to statement has an immediate consequence that it
> becomes terribly hard to find a meaningful set of coordinates in which to
> describe the process progress.
-->
> 对 go to 语句不加约束的使用，有一个直接后果：要找到一套有意义的坐标来描述过程进展，变得极其困难。

<!--
He doesn't prove that this is hard, or say why. He just says it. He does say
that one approach is unsatisfactory:
-->
他没有证明这很难，也没说为什么。他只是这么说。他倒是说有一种做法不尽如人意：

<!--
> With the go to statement one can, of course, still describe the progress
> uniquely by a counter counting the number of actions performed since program
> start (viz. a kind of normalized clock). The difficulty is that such a
> coordinate, although unique, is utterly unhelpful.
-->
> 有了 go to 语句，当然仍可用一个计数器唯一地描述进展——自程序启动以来执行的动作数（亦即一种归一化时钟）。困难在于：这样的坐标虽然唯一，却完全无用。

<!--
But... that's effectively what loop counters do, and he was fine with those.
It's not like every loop is a simple "for every integer from 0 to 10"
incrementing count. Many are `while` loops with complex conditionals.
-->
可是……那基本上正是循环计数器在做的事，而他对那些倒挺满意。又不是每个循环都是简单的“从 0 到 10 每个整数”递增计数。许多是带复杂条件的 `while` 循环。

<!--
Taking an example close to home, consider the core bytecode execution loop at
the heart of clox. Dijkstra argues that that loop is tractable because we can
simply count how many times the loop has run to reason about its progress. But
that loop runs once for each executed instruction in some user's compiled Lox
program. Does knowing that it executed 6,201 bytecode instructions really tell
us VM maintainers *anything* edifying about the state of the interpreter?
-->
举个近在身边的例子：想想 clox 核心的字节码执行循环。Dijkstra 主张该循环好处理，因为我们可以简单数循环跑了多少次来推理其进展。可那个循环对用户编译的 Lox 程序里每条已执行指令都跑一次。知道它执行了 6,201 条字节码指令，真的能告诉我们这些虚拟机维护者关于解释器状态的*任何*教益吗？

<!--
In fact, this particular example points to a deeper truth. Böhm and Jacopini
[proved][] that *any* control flow using goto can be transformed into one using
just sequencing, loops, and branches. Our bytecode interpreter loop is a living
example of that proof: it implements the unstructured control flow of the clox
bytecode instruction set without using any gotos itself.
-->
事实上，这个例子指向更深的真相。Böhm 与 Jacopini [证明了][proved]：*任何*使用 goto 的控制流，都能变换成只用顺序、循环与分支的形式。我们的字节码解释器循环就是该证明的活例：它实现了 clox 字节码指令集的非结构化控制流，自身却不用任何 goto。

[proved]: https://en.wikipedia.org/wiki/Structured_program_theorem

<!--
That seems to offer a counter-argument to Dijkstra's claim: you *can* define a
correspondence for a program using gotos by transforming it to one that doesn't
and then use the correspondence from that program, which -- according to him --
is acceptable because it uses only branches and loops.
-->
这似乎给 Dijkstra 的主张提供了反论：你*可以*为使用 goto 的程序定义对应关系——先把它变换成不用 goto 的程序，再使用那个程序的对应关系；而据他所说，后者可接受，因为它只用分支与循环。

<!--
But, honestly, my argument here is also weak. I think both of us are basically
doing pretend math and using fake logic to make what should be an empirical,
human-centered argument. Dijkstra is right that some code using goto is really
bad. Much of that could and should be turned into clearer code by using
structured control flow.
-->
不过说实话，我这儿的论证也很弱。我想我们俩基本上都在假装做数学，用假逻辑去支撑本该是经验性、以人为中心的论证。Dijkstra 说得对：有些用 goto 的代码确实很糟。其中许多可以、也应当用结构化控制流改成更清晰的代码。

<!--
By eliminating goto completely from languages, you're definitely prevented from
writing bad code using gotos. It may be that forcing users to use structured
control flow and making it an uphill battle to write goto-like code using those
constructs is a net win for all of our productivity.
-->
从语言里彻底消灭 goto，你当然就不会再用 goto 写出坏代码。或许，强迫用户使用结构化控制流，并让用那些构造写出类似 goto 的代码变得艰难上坡——对我们大家的生产力来说，是净赢。

<!--
But I do wonder sometimes if we threw out the baby with the bathwater. In the
absence of goto, we often resort to more complex structured patterns. The
"switch inside a loop" is a classic one. Another is using a guard variable to
exit out of a series of nested loops:
-->
可我有时仍会想：我们是不是连洗澡水带婴儿一起泼掉了。没有 goto 时，我们常常诉诸更复杂的结构化模式。“循环里套 switch”是经典一例。另一例是用守卫变量退出一串嵌套循环：

<span name="break">
</span>

```c
// See if the matrix contains a zero.
bool found = false;
for (int x = 0; x < xSize; x++) {
  for (int y = 0; y < ySize; y++) {
    for (int z = 0; z < zSize; z++) {
      if (matrix[x][y][z] == 0) {
        printf("found");
        found = true;
        break;
      }
    }
    if (found) break;
  }
  if (found) break;
}
```

<!--
Is that really better than:
-->
这真的比下面更好吗：

```c
for (int x = 0; x < xSize; x++) {
  for (int y = 0; y < ySize; y++) {
    for (int z = 0; z < zSize; z++) {
      if (matrix[x][y][z] == 0) {
        printf("found");
        goto done;
      }
    }
  }
}
done:
```

<aside name="break">

<!--
You could do this without `break` statements -- themselves a limited goto-ish
construct -- by inserting `!found &&` at the beginning of the condition clause
of each loop.
-->
你也可以不用 `break` 语句——它本身就是一种受限的、有点像 goto 的构造——在每个循环的条件子句开头插入 `!found &&`。

</aside>

<!--
I guess what I really don't like is that we're making language design and
engineering decisions today based on fear. Few people today have any subtle
understanding of the problems and benefits of goto. Instead, we just think it's
"considered harmful". Personally, I've never found dogma a good starting place
for quality creative work.
-->
我想我真正不喜欢的是：我们今天在基于恐惧做语言设计与工程决策。如今很少有人对 goto 的问题与好处有细致理解。相反，我们只觉得它“被认为有害”。就我个人而言，我从未觉得教条是优质创造性工作的好起点。

</div>
