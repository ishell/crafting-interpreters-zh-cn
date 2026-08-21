# Lox 程序设计语言

<!--
> What nicer thing can you do for somebody than make them breakfast?
>
> <cite>Anthony Bourdain</cite>
-->
> 有什么能比得上为饥肠辘辘的人端上一份丰盛早餐更好的事呢？
>
> <cite>安东尼·波登<em>（美国知名大厨）</em></cite>

<!--
We'll spend the rest of this book illuminating every dark and sundry corner of
the Lox language, but it seems cruel to have you immediately start grinding out
code for the interpreter without at least a glimpse of what we're going to end
up with.
-->
本书接下来的部分将仔细探索 Lox 程序语言实现的角角落落，但是在真正动手编写解释器代码之前，还是让我们来好好地认识一下这个我们将要实现的程序语言吧。

<!--
At the same time, I don't want to drag you through reams of language lawyering
and specification-ese before you get to touch your text <span
name="home">editor</span>. So this will be a gentle, friendly introduction to
Lox. It will leave out a lot of details and edge cases. We've got plenty of time
for those later.
-->
在当下，你还没有真正上手编写<span name="home">代码</span>之前，我不想先让你陷入到 Lox 程序语言的各种细节与语言规范里头去。所以本章是对 Lox 程序语言的一个温和、友好的介绍，大量语法细节与边界条件让我们放到后面具体实现时再详细阐述。

<aside name="home">

如果都不能上手编写几行 Lox 代码运行起来看一看，那本篇的内容也太枯燥乏味了，可是可是，你手上还没有一支 Lox 解释器呀，你都还没有开始构建它呢！

不打紧，你可以用[我写好的 Lox 解释器][repo]上手尝试。

<!--
A tutorial isn't very fun if you can't try the code out yourself. Alas, you
don't have a Lox interpreter yet, since you haven't built one!

Fear not. You can use [mine][repo].
-->

[repo]: https://github.com/munificent/craftinginterpreters

</aside>

<!--
-- Hello, Lox
-->
## 你好，Lox

<!--
Here's your very first taste of <span name="salmon">Lox</span>:
-->
这是你首次<span name="salmon">接触</span> Lox 程序设计语言。

<aside name="salmon">

<!--
Your first taste of Lox, the language, that is. I don't know if you've ever had
the cured, cold-smoked salmon before. If not, give it a try too.
-->
这是你首次尝鲜 Lox 程序语言，不知道你之前有没有吃过腌制的冷熏三文鱼，没吃过可以尝试一下。

</aside>

```lox
// Your first Lox program!
print "Hello, world!";
```

<!--
As that `//` line comment and the trailing semicolon imply, Lox's syntax is a
member of the C family. (There are no parentheses around the string because
`print` is a built-in statement, and not a library function.)
-->
行注释`//`与句末分号`;`标示着 Lox 语法偏向 C 系，Lox 是一门类 C 的程序语言（字符串两边没有带小括号，这是因为`print`是一个内建语句，而不是一个库函数）。

<!--
Now, I won't claim that <span name="c">C</span> has a *great* syntax. If we
wanted something elegant, we'd probably mimic Pascal or Smalltalk. If we wanted
to go full Scandinavian-furniture-minimalism, we'd do a Scheme. Those all have
their virtues.
-->
我可不会声称 <span name="c">C</span> 有着*了不起*的语法。如果我们想要更加优雅的语法风格，Lox 可能偏向 Pascal 或者 Smalltalk；如果我们想要极简主义的语法风格，Lox 可能更偏向 Scheme。这些程序语言都有各自的可取之处。

<aside name="c">

<!--
I'm surely biased, but I think Lox's syntax is pretty clean. C's most egregious
grammar problems are around types. Dennis Ritchie had this idea called
"[declaration reflects use][use]", where variable declarations mirror the
operations you would have to perform on the variable to get to a value of the
base type. Clever idea, but I don't think it worked out great in practice.
-->
我的想法一定带有些主观情绪，但是我认为 Lox 的语法相当简洁清晰。C 语法最大的问题在于类型，丹尼斯·里奇将 C 语言类型的设计想法称为[”声明反映用法“][use]：变量声明直接反映出如果对变量取值应该采取的操作。这真是一个绝妙的想法，但在具体实践中工作得并不是很好，许多变量声明不够清晰难以理解。

[use]: http://softwareengineering.stackexchange.com/questions/117024/why-was-the-c-syntax-for-arrays-pointers-and-functions-designed-this-way

<!--
Lox doesn't have static types, so we avoid that.
-->
Lox 并不是静态类型语言，所以我们可以很好地避免了这个问题。

</aside>

<!--
What C-like syntax has instead is something you'll often find more valuable
in a language: *familiarity*. I know you are already comfortable with that style
because the two languages we'll be using to *implement* Lox -- Java and C --
also inherit it. Using a similar syntax for Lox gives you one less thing to
learn.
-->
类 C 语法最大的优势在于，它可以为读者带来：*熟悉感*。我知道你已经对我们将要用来*实现*  Lox 的两门程序语言 Java、C 非常熟悉了，Lox 采用与 C、Java 一脉相承的类 C 语法，这将为读者减少很多心智负担。

<!--
-- A High-Level Language
-->
## 一门高阶的程序设计语言

<!--
While this book ended up bigger than I was hoping, it's still not big enough to
fit a huge language like Java in it. In order to fit two complete
implementations of Lox in these pages, Lox itself has to be pretty compact.
-->
当我写完这本书时，书本的篇幅超出了我的预期，但这本书仍然没有达到够容纳类似 Java 这样大型程序语言实现的厚度。为了能在本书有限的篇幅里包含两种 Lox 语言的完整实现，Lox 语言本身必须被设计得小巧紧凑。

<!--
When I think of languages that are small but useful, what comes to mind are
high-level "scripting" languages like <span name="js">JavaScript</span>, Scheme,
and Lua. Of those three, Lox looks most like JavaScript, mainly because most
C-syntax languages do. As we'll learn later, Lox's approach to scoping hews
closely to Scheme. The C flavor of Lox we'll build in [Part III][] is heavily
indebted to Lua's clean, efficient implementation.
-->
当我思考哪些程序语言既小巧又实用的时候，我脑海中浮现出像 <span name="js">JavaScript</span>、Scheme、Lua 这样的高级“脚本”语言。在这三者之中，Lox 与 JavaScript 最为相像，大多数类 C 语法的脚本语言都像 JavaScript。当我们继续深入，就会发现 Lox 的作用域界定与 Scheme 相似。而在本书[第三部分][part iii]，我们使用 C 语言编写的 Lox 解释器，在具体实现细节上大量参考借鉴了 Lua 清晰高效的代码实现。

[part iii]: a-bytecode-virtual-machine.html

<aside name="js">

<!--
Now that JavaScript has taken over the world and is used to build ginormous
applications, it's hard to think of it as a "little scripting language". But
Brendan Eich hacked the first JS interpreter into Netscape Navigator in *ten
days* to make buttons animate on web pages. JavaScript has grown up since then,
but it was once a cute little language.
-->
如今，JavaScript 已经统治了世界，被用以构建超大型应用程序，认为 JavaScript 只是一门“小型脚本语言”的认知已经不太合适了。但在 JavaScript 最初诞生的那会儿，布兰登·艾奇为了能让网页上的按钮动起来，仅花了*十天*时间就设计实现了第一支 JS 解释器，放进网景浏览器里。在那时，JS 倒称得上是一支小巧可爱的小脚本语言，但随着 Web 技术的发展，如今的 JavaScript 已经变得异常庞大了。

<!--
Because Eich slapped JS together with roughly the same raw materials and time as
an episode of MacGyver, it has some weird semantic corners where the duct tape
and paper clips show through. Things like variable hoisting, dynamically bound
`this`, holes in arrays, and implicit conversions.
-->
可能是因为艾奇当初设计 JavaScript 所花的时间与心思太少了，就像《玉面飞龙》电视连续剧那样，JS 语言在许多语法角落和实现细节方面都留下了不少坑，如：变量作用域、`this`动态绑定、数组方面的坑、隐式类型转换等等。

<!--
I had the luxury of taking my time on Lox, so it should be a little cleaner.
-->
我花了很多时间在 Lox 语言设计上，所以 Lox 应该会比 JavaScript 更清晰一些，嘻嘻。

</aside>

<!--
Lox shares two other aspects with those three languages:
-->
在以下两个方面，Lox 也与这三门程序语言有着同样的理念。

<!--
--- Dynamic typing
-->
### 动态类型

<!--
Lox is dynamically typed. Variables can store values of any type, and a single
variable can even store values of different types at different times. If you try
to perform an operation on values of the wrong type -- say, dividing a number by
a string -- then the error is detected and reported at runtime.
-->
Lox 是一门动态类型的程序语言。变量可以存储任意类型的数据，也可以在程序运行的任意时刻改变其存储的数据类型。如果你在不兼容数据类型上执行了一个错误操作，比如说：将一个数字除以一枚字符串，那么该错误将在运行时被捕获和抛出。

<!--
There are plenty of reasons to like <span name="static">static</span> types, but
they don't outweigh the pragmatic reasons to pick dynamic types for Lox. A
static type system is a ton of work to learn and implement. Skipping it gives
you a simpler language and a shorter book. We'll get our interpreter up and
executing bits of code sooner if we defer our type checking to runtime.
-->
<span name="static">静态类型</span>有着许多令人喜爱的理由，但在实践上，我还是为 Lox 选择了动态类型。实现一个完备的静态类型系统需要大量的背景知识、深厚的代码功底。忽略静态类型，程序语言会变得更加简单，这本书也会变得更薄一些。将类型检查下推到运行时，可以让我们快速构建起一支可以执行代码的语言解释器。

<aside name="static">

<!--
After all, the two languages we'll be using to *implement* Lox are both
statically typed.
-->
毕竟，两门我们用来*实现* Lox 的程序语言（Java、C）都是静态类型的。

</aside>

<!--
--- Automatic memory management
-->
### 自动内存管理

<!--
High-level languages exist to eliminate error-prone, low-level drudgery, and what
could be more tedious than manually managing the allocation and freeing of
storage? No one rises and greets the morning sun with, "I can't wait to figure
out the correct place to call `free()` for every byte of memory I allocate
today!"
-->
高阶程序语言诞生的目的之一便是为了消除易出错的底层操作，还有什么比手动管理内存的分配释放更令人烦心的事情呢？没有人愿意早晨起来这么互相打招呼：“我迫不及待想为我今天申请的每块内存找个合适的地方调用`free()`函数啦！”

<!--
There are two main <span name="gc">techniques</span> for managing memory:
**reference counting** and **tracing garbage collection** (usually just called
**garbage collection** or **GC**). Ref counters are much simpler to implement --
I think that's why Perl, PHP, and Python all started out using them. But, over
time, the limitations of ref counting become too troublesome. All of those
languages eventually ended up adding a full tracing GC, or at least enough of
one to clean up object cycles.
-->
目前主要有两类技术用以管理内存：**引用计数（Reference Counting）** 和 **垃圾回收（Tracing Garbage Collection、Garbage Collection、GC）**。引用计数在实现上更加简便，我想这也是为什么 Perl、PHP、Python 起初都使用引用计数管理内存的原因。但是随着语言的发展，引用计数的局限性越来越明显，所以到最后，这些程序语言都添加上了完整的垃圾回收器，至少也足以清理对象之间的循环引用。

<aside name="gc">

<!--
In practice, ref counting and tracing are more ends of a continuum than
opposing sides. Most ref counting systems end up doing some tracing to handle
cycles, and the write barriers of a generational collector look a bit like
retain calls if you squint.
-->
在具体实践中，引用计数和追踪回收更像是连续光谱的两端，而非截然对立。多数引用计数系统最终都会做一些追踪来处理循环引用；而若你眯着眼看，分代回收器的写屏障，也有几分像 retain 调用。

<!--
For lots more on this, see "[A Unified Theory of Garbage Collection][gc]" (PDF).
-->
更多关于这方面的讨论，参看这篇论文：[A Unified Theory of Garbage Collection][gc] (PDF)。

[gc]: https://researcher.watson.ibm.com/researcher/files/us-bacon/Bacon04Unified.pdf

</aside>

<!--
Tracing garbage collection has a fearsome reputation. It *is* a little harrowing
working at the level of raw memory. Debugging a GC can sometimes leave you
seeing hex dumps in your dreams. But, remember, this book is about dispelling
magic and slaying those monsters, so we *are* going to write our own garbage
collector. I think you'll find the algorithm is quite simple and a lot of fun to
implement.
-->
“垃圾回收（GC）”声名远播，让人心生畏惧，它需要开发者真正面向内存做一些细致的工作，调试垃圾回收器能让你做梦都能梦到程序的 16 进制转储调试信息。但是无需担心，本书就是为了揭开魔法、消灭怪兽的。我们将编写自己的垃圾回收器，你会发现，垃圾回收用到的算法其实非常简单，实现起来也非常有趣。

<!--
-- Data Types
-->
## 数据类型

<!--
In Lox's little universe, the atoms that make up all matter are the built-in
data types. There are only a few:
-->
在 Lox 的小小宇宙中，构成宇宙的原子即是内置数据类型。Lox 目前只有几种简单的内置数据类型：

<!--
*   **<span name="bool">Booleans</span>.** You can't code without logic and you
    can't logic without Boolean values. "True" and "false", the yin and yang of
    software. Unlike some ancient languages that repurpose an existing type to
    represent truth and falsehood, Lox has a dedicated Boolean type. We may
    be roughing it on this expedition, but we aren't *savages*.
-->
*   **<span name="bool">布尔类型（Boolean）</span>**。没有布尔类型，就无法表示逻辑，无法进行逻辑判断，就难以编写代码。“True” 与 “False” 就像是程序的“阴”与“阳”。许多古老的程序语言使用已经存在的数据类型表示逻辑真假（如：C 语言），Lox 没有选择这么做，Lox 有着专用的布尔类型，虽然实现上较为粗糙，但对比古老的程序语言们，我们足够先进，一点也不老土。

    <aside name="bool">

    <!--
    Boolean variables are the only data type in Lox named after a person, George
    Boole, which is why "Boolean" is capitalized. He died in 1864, nearly a
    century before digital computers turned his algebra into electricity. I
    wonder what he'd think to see his name all over billions of lines of Java
    code.
    -->
    布尔类型是唯一一种使用人名来命名的数据类型：乔治·布尔（George Boole），人们使用“Boolean”一词（人名，首字母大写）纪念他。乔治·布尔于 1864 年去世，过了一个多世纪，人们将布尔代数在电路上实现，造出了现代电子计算机。我很好奇，如果乔治·布尔生活在现今，看到成千上万的代码行里都镌刻着他的名字（特别是 Java 代码），会作何感想呢。

    </aside>

    <!--
    There are two Boolean values, obviously, and a literal for each one.
    -->
    显而易见的，布尔类型只有两个值：`true`和`false`。

    ```lox
    true;  // Not false.
    false; // Not *not* false.
    ```

<!--
*   **Numbers.** Lox has only one kind of number: double-precision floating
    point. Since floating-point numbers can also represent a wide range of
    integers, that covers a lot of territory, while keeping things simple.
-->
*   **数字类型（Numbers）**。Lox 程序语言只有一种数字类型：双精度浮点数。浮点数也可以覆盖很大范围的整数，为了让事情变得更加简单，我们只用这一种数。

    <!--
    Full-featured languages have lots of syntax for numbers -- hexadecimal,
    scientific notation, octal, all sorts of fun stuff. We'll settle for basic
    integer and decimal literals.
    -->
    功能全面的通用程序设计语言通常有着很多表示数字的语法：十六进制数、科学计数法、八进制数等等，这些数字表示法挺有趣的，但在这里，我们只支持最基本的十进制整数与小数。

    ```lox
    1234;  // An integer.
    12.34; // A decimal number.
    ```
<!--
*   **Strings.** We've already seen one string literal in the first example.
    Like most languages, they are enclosed in double quotes.
-->
*   **字符串类型（String）**。在本章开头部分的第一个程序示例中，我们就已经见过字符串类型了。与大部分程序语言一样，字符串字面量由两个双引号包裹。

    ```lox
    "I am a string";
    "";    // The empty string.
    "123"; // This is a string, not a number.
    ```

    <!--
    As we'll see when we get to implementing them, there is quite a lot of
    complexity hiding in that innocuous sequence of <span
    name="char">characters</span>.
    -->
    当我们真正开始着手实现字符串类型时就会发现，在看似简单的<span name="char">字符序列</span>下，隐藏着许多复杂的实现细节。

    <aside name="char">

    <!--
    Even that word "character" is a trickster. Is it ASCII? Unicode? A
    code point or a "grapheme cluster"? How are characters encoded? Is each
    character a fixed size, or can they vary?
    -->
    甚至是“字符”一词都极具欺骗性。字符是 ASCII 码还是 Unicode 万国码？是字符码点（Code Point）还是字形簇（Grapheme Cluster）？字符如何进行编码？单字符是定长还是变长？

    </aside>

<!--
*   **Nil.** There's one last built-in value who's never invited to the party
    but always seems to show up. It represents "no value". It's called "null" in
    many other languages. In Lox we spell it `nil`. (When we get to implementing
    it, that will help distinguish when we're talking about Lox's `nil` versus
    Java or C's `null`.)
-->
*   **空类型（Nil）**。 最后一个内置数据类型是空类型，虽然我们经常会忘记它，但空类型总是会在不经意间跳出来。空类型的含义是：没有值。在很多其他的程序语言里，空类型使用`null`表示，在 Lox 中，我们使用`nil`表示空类型（用以实现 Lox 的两门语言 Java、C 都保留了`null`关键字，所以我们换个词加以区分）。

    <!--
    There are good arguments for not having a null value in a language since
    null pointer errors are the scourge of our industry. If we were doing a
    statically typed language, it would be worth trying to ban it. In a
    dynamically typed one, though, eliminating it is often more annoying
    than having it.
    -->
    有许多合理的理由告诉我们，不应该在程序语言中引入空值`null`，空指针异常（Null Pointer Errors）给工业界带来了巨大的灾难。如果我们构建的是一门静态类型语言，倒是可以尝试着消除空值`null`。但对于一门动态类型程序语言来说，消除空值`null`会令你陷入更大的麻烦之中，得不偿失，不如引入空值`null`。

<!--
-- Expressions
-->
## 表达式

<!--
If built-in data types and their literals are atoms, then **expressions** must
be the molecules. Most of these will be familiar.
-->
如果说内置数据类型及其字面量是原子，那么**表达式**便是分子。下面介绍的大多数表达式，你应该都再熟悉不过了。

<!--
### Arithmetic
-->
### 算术运算

<!--
Lox features the basic arithmetic operators you know and love from C and other
languages:
-->
Lox 拥有你在 C 及其他语言中早已耳熟能详的基本算术运算符：

```lox
add + me;
subtract - me;
multiply * me;
divide / me;
```

<!--
The subexpressions on either side of the operator are **operands**. Because
there are *two* of them, these are called **binary** operators. (It has nothing
to do with the ones-and-zeroes use of "binary".) Because the operator is <span
name="fixity">fixed</span> *in* the middle of the operands, these are also
called **infix** operators (as opposed to **prefix** operators where the
operator comes before the operands, and **postfix** where it comes after).
-->
运算符两侧的子表达式称为**操作数**（operands）。由于操作数有*两个*，这类运算符被称为**二元运算符**（binary operators）——这与“二进制”里的 binary 毫无关系。又因为运算符<span name="fixity">固定</span>在操作数*中间*，它们也被称为**中缀运算符**（infix operators），与之相对的是**前缀运算符**（prefix operators，运算符在操作数之前）和**后缀运算符**（postfix operators，运算符在操作数之后）。

<aside name="fixity">

<!--
There are some operators that have more than two operands and the operators are
interleaved between them. The only one in wide usage is the "conditional" or
"ternary" operator of C and friends:
-->
有些运算符拥有两个以上的操作数，运算符穿插其间。广泛使用的例子只有 C 及其同族语言里的“条件运算符”或“三目运算符”：

```c
condition ? thenArm : elseArm;
```

<!--
Some call these **mixfix** operators. A few languages let you define your own
operators and control how they are positioned -- their "fixity".
-->
有人称这类运算符为**混合定址运算符**（mixfix operators）。少数语言允许你自定义运算符，并控制它们的位置——即所谓的“定址”（fixity）。

</aside>

<!--
One arithmetic operator is actually *both* an infix and a prefix one. The `-`
operator can also be used to negate a number.
-->
有一个算术运算符实际上*既是*中缀又是前缀：`-` 运算符也可以用来对数字取负。

```lox
-negateMe;
```

<!--
All of these operators work on numbers, and it's an error to pass any other
types to them. The exception is the `+` operator -- you can also pass it two
strings to concatenate them.
-->
这些运算符都作用于数字，传入其他类型会报错。唯一的例外是 `+` 运算符——你也可以给它两个字符串，用来拼接它们。

<!--
### Comparison and equality
-->
### 比较与相等

<!--
Moving along, we have a few more operators that always return a Boolean result.
We can compare numbers (and only numbers), using Ye Olde Comparison Operators.
-->
继续往下，还有几种运算符始终返回布尔值。我们可以用那些古老而熟悉的比较运算符来比较数字——而且*只能*比较数字。

```lox
less < than;
lessThan <= orEqual;
greater > than;
greaterThan >= orEqual;
```

<!--
We can test two values of any kind for equality or inequality.
-->
我们可以检验任意类型的两个值是否相等或不等。

```lox
1 == 2;         // false.
"cat" != "dog"; // true.
```

<!--
Even different types.
-->
即便类型不同也可以。

```lox
314 == "pi"; // false.
```

<!--
Values of different types are *never* equivalent.
-->
不同类型的值*永远不会*被视为等价。

```lox
123 == "123"; // false.
```

<!--
I'm generally against implicit conversions.
-->
我通常不太赞成隐式类型转换。

<!--
### Logical operators
-->
### 逻辑运算符

<!--
The not operator, a prefix `!`, returns `false` if its operand is true, and vice
versa.
-->
逻辑非运算符是前缀形式的 `!`：若操作数为真则返回 `false`，反之亦然。

```lox
!true;  // false.
!false; // true.
```

<!--
The other two logical operators really are control flow constructs in the guise
of expressions. An <span name="and">`and`</span> expression determines if two
values are *both* true. It returns the left operand if it's false, or the
right operand otherwise.
-->
另外两种逻辑运算符，本质上是以表达式面目出现的控制流结构。<span name="and">`and`</span> 表达式判断两个值是否*都为*真：若左操作数为假则返回左操作数，否则返回右操作数。

```lox
true and false; // false.
true and true;  // true.
```

<!--
And an `or` expression determines if *either* of two values (or both) are true.
It returns the left operand if it is true and the right operand otherwise.
-->
`or` 表达式则判断两个值中是否*至少有一个*（或两个都为）真：若左操作数为真则返回左操作数，否则返回右操作数。

```lox
false or false; // false.
true or false;  // true.
```

<aside name="and">

<!--
I used `and` and `or` for these instead of `&&` and `||` because Lox doesn't use
`&` and `|` for bitwise operators. It felt weird to introduce the
double-character forms without the single-character ones.
-->
我用 `and` 和 `or`，而不是 `&&` 和 `||`，因为 Lox 没有使用 `&` 和 `|` 作为按位运算符。在没有单字符形式的情况下引入双字符形式，总让我觉得有些别扭。

<!--
I also kind of like using words for these since they are really control flow
structures and not simple operators.
-->
而且我挺喜欢用单词来表示它们——毕竟它们真的是控制流结构，而不是简单的运算符。

</aside>

<!--
The reason `and` and `or` are like control flow structures is that they
**short-circuit**. Not only does `and` return the left operand if it is false,
it doesn't even *evaluate* the right one in that case. Conversely
(contrapositively?), if the left operand of an `or` is true, the right is
skipped.
-->
`and` 和 `or` 之所以像控制流结构，是因为它们会**短路**（short-circuit）。`and` 在左操作数为假时不仅返回左操作数，甚至*不会*去求值右操作数。反过来说（逆否命题？），若 `or` 的左操作数为真，右操作数也会被跳过。

<!--
### Precedence and grouping
-->
### 优先级与分组

<!--
All of these operators have the same precedence and associativity that you'd
expect coming from C. (When we get to parsing, we'll get *way* more precise
about that.) In cases where the precedence isn't what you want, you can use `()`
to group stuff.
-->
所有这些运算符的优先级和结合性，都与你在 C 语言中所预期的一致。（等到语法分析那一章，我们会*精确得多*地说明这一点。）若优先级不符合你的意图，可以用 `()` 把表达式分组。

```lox
var average = (min + max) / 2;
```

<!--
Since they aren't very technically interesting, I've cut the remainder of the
typical operator menagerie out of our little language. No bitwise, shift,
modulo, or conditional operators. I'm not grading you, but you will get bonus
points in my heart if you augment your own implementation of Lox with them.
-->
由于它们在技术上并不算多有趣，我把典型运算符家族里其余的成员都从这门小语言里裁掉了——没有按位、移位、取模或条件运算符。我不会给你打分，但若你在自己的 Lox 实现里加上它们，在我心里你会加分。

<!--
Those are the expression forms (except for a couple related to specific features
that we'll get to later), so let's move up a level.
-->
表达式形式就这些了（另有几个与特定特性相关、我们稍后再讲的），让我们往上一层走。

<!--
## Statements
-->
## 语句

<!--
Now we're at statements. Where an expression's main job is to produce a *value*,
a statement's job is to produce an *effect*. Since, by definition, statements
don't evaluate to a value, to be useful they have to otherwise change the world
in some way -- usually modifying some state, reading input, or producing output.
-->
现在轮到语句了。表达式的主要职责是产生一个*值*，语句的职责则是产生一个*效果*。按定义，语句不求值，若要派上用场，它们就必须以某种方式改变世界——通常是修改状态、读取输入或产生输出。

<!--
You've seen a couple of kinds of statements already. The first one was:
-->
你已经见过几种语句了。第一种是：

```lox
print "Hello, world!";
```

<!--
A <span name="print">`print` statement</span> evaluates a single expression
and displays the result to the user. You've also seen some statements like:
-->
<span name="print">`print` 语句</span>对单个表达式求值，并将结果显示给用户。你还见过这样的语句：

<aside name="print">

<!--
Baking `print` into the language instead of just making it a core library
function is a hack. But it's a *useful* hack for us: it means our in-progress
interpreter can start producing output before we've implemented all of the
machinery required to define functions, look them up by name, and call them.
-->
把 `print` 内建进语言，而不是做成核心库函数，算是一种取巧。但对我们而言，这是*有用*的取巧：这意味着在我们实现定义函数、按名查找并调用函数所需的全部机制之前，尚在搭建中的解释器就能开始产生输出了。

</aside>

```lox
"some expression";
```

<!--
An expression followed by a semicolon (`;`) promotes the expression to
statement-hood. This is called (imaginatively enough), an **expression
statement**.
-->
表达式后面跟一个分号（`;`），就把表达式提升为语句——够有想象力的名字：**表达式语句**（expression statement）。

<!--
If you want to pack a series of statements where a single one is expected, you
can wrap them up in a block.
-->
若想在只期望一条语句的地方塞入一系列语句，可以把它们包在一个块里。

```lox
{
  print "One statement.";
  print "Two statements.";
}
```

<!--
Blocks also affect scoping, which leads us to the next section...
-->
块也会影响作用域，这就引出了下一节……

<!--
## Variables
-->
## 变量

<!--
You declare variables using `var` statements. If you <span
name="omit">omit</span> the initializer, the variable's value defaults to `nil`.
-->
你用 `var` 语句声明变量。若<span name="omit">省略</span>初始化器，变量的值默认为 `nil`。

<aside name="omit">

<!--
This is one of those cases where not having `nil` and forcing every variable to
be initialized to some value would be more annoying than dealing with `nil`
itself.
-->
这正是那种情形：若没有 `nil`、强迫每个变量都必须初始化为某个值，会比直接面对 `nil` 本身更烦人。

</aside>

```lox
var imAVariable = "here is my value";
var iAmNil;
```

<!--
Once declared, you can, naturally, access and assign a variable using its name.
-->
声明之后，你自然可以通过变量名访问并赋值。

<span name="breakfast"></span>

```lox
var breakfast = "bagels";
print breakfast; // "bagels".
breakfast = "beignets";
print breakfast; // "beignets".
```

<aside name="breakfast">

<!--
Can you tell that I tend to work on this book in the morning before I've had
anything to eat?
-->
看得出来吗？我往往是在早上还没吃过任何东西的时候写这本书的。

</aside>

<!--
I won't get into the rules for variable scope here, because we're going to spend
a surprising amount of time in later chapters mapping every square inch of the
rules. In most cases, it works like you would expect coming from C or Java.
-->
此处我不展开变量作用域的规则，因为在后面的章节里，我们会花出奇地多的时间，把规则的每一寸地图都画出来。在大多数情况下，它的表现与你在 C 或 Java 中的预期一致。

<!--
## Control Flow
-->
## 控制流

<!--
It's hard to write <span name="flow">useful</span> programs if you can't skip
some code or execute some more than once. That means control flow. In addition
to the logical operators we already covered, Lox lifts three statements straight
from C.
-->
若不能跳过某些代码，或让某些代码执行不止一次，就很难写出<span name="flow">有用</span>的程序。这就需要控制流。除了我们已经讲过的逻辑运算符，Lox 还直接从 C 语言里搬来了三种语句。

<aside name="flow">

<!--
We already have `and` and `or` for branching, and we *could* use recursion to
repeat code, so that's theoretically sufficient. It would be pretty awkward to
program that way in an imperative-styled language, though.

Scheme, on the other hand, has no built-in looping constructs. It *does* rely on
recursion for repetition. Smalltalk has no built-in branching constructs, and
relies on dynamic dispatch for selectively executing code.
-->
我们已有 `and` 和 `or` 用于分支，也*可以*用递归来重复代码，理论上这就够了。但在命令式风格的语言里，那样写程序会相当别扭。

Scheme 则没有内建的循环结构，重复代码*确实*依赖递归。Smalltalk 没有内建的分支结构，靠动态分派来选择性执行代码。

</aside>

<!--
An `if` statement executes one of two statements based on some condition.
-->
`if` 语句根据某个条件，执行两条语句中的一条。

```lox
if (condition) {
  print "yes";
} else {
  print "no";
}
```

<!--
A `while` <span name="do">loop</span> executes the body repeatedly as long as
the condition expression evaluates to true.
-->
`while` <span name="do">循环</span>在条件表达式为真时，反复执行循环体。

```lox
var a = 1;
while (a < 10) {
  print a;
  a = a + 1;
}
```

<aside name="do">

<!--
I left `do while` loops out of Lox because they aren't that common and wouldn't
teach you anything that you won't already learn from `while`. Go ahead and add
it to your implementation if it makes you happy. It's your party.
-->
我把 `do while` 循环排除在 Lox 之外，因为它们并不常见，而且你从 `while` 里能学到的东西，它们也教不了你什么。若加上它让你开心，尽可以在自己的实现里添加——那是你的派对。

</aside>

<!--
Finally, we have `for` loops.
-->
最后，还有 `for` 循环。

```lox
for (var a = 1; a < 10; a = a + 1) {
  print a;
}
```

<!--
This loop does the same thing as the previous `while` loop. Most modern
languages also have some sort of <span name="foreach">`for-in`</span> or
`foreach` loop for explicitly iterating over various sequence types. In a real
language, that's nicer than the crude C-style `for` loop we got here. Lox keeps
it basic.
-->
这个循环与前面的 `while` 循环做的事相同。大多数现代语言还有某种 <span name="foreach">`for-in`</span> 或 `foreach` 循环，用于显式遍历各种序列类型。在真正的语言里，那比这里这种粗粝的 C 风格 `for` 循环更讨喜。Lox 保持基础就好。

<aside name="foreach">

<!--
This is a concession I made because of how the implementation is split across
chapters. A `for-in` loop needs some sort of dynamic dispatch in the iterator
protocol to handle different kinds of sequences, but we don't get that until
after we're done with control flow. We could circle back and add `for-in` loops
later, but I didn't think doing so would teach you anything super interesting.
-->
这是我在章节划分上作出的妥协。`for-in` 循环需要在迭代器协议里做某种动态分派，以处理不同种类的序列，但那要等到控制流章节结束之后才有。我们本可以回头加上 `for-in` 循环，但我觉得那样教不了你什么特别有意思的东西。

</aside>

<!--
## Functions
-->
## 函数

<!--
A function call expression looks the same as it does in C.
-->
函数调用表达式与 C 语言中的写法相同。

```lox
makeBreakfast(bacon, eggs, toast);
```

<!--
You can also call a function without passing anything to it.
-->
你也可以不传任何参数就调用函数。

```lox
makeBreakfast();
```

<!--
Unlike in, say, Ruby, the parentheses are mandatory in this case. If you leave them
off, it doesn't *call* the function, it just refers to it.
-->
与 Ruby 等不同，此处括号是必需的。若省略括号，并不会*调用*函数，而只是引用它。

<!--
A language isn't very fun if you can't define your own functions. In Lox, you do
that with <span name="fun">`fun`</span>.
-->
若不能定义自己的函数，一门语言就谈不上多有趣。在 Lox 中，你用 <span name="fun">`fun`</span> 来定义函数。

<aside name="fun">

<!--
I've seen languages that use `fn`, `fun`, `func`, and `function`. I'm still
hoping to discover a `funct`, `functi`, or `functio` somewhere.
-->
我见过用 `fn`、`fun`、`func` 和 `function` 的语言。我仍希望能在某处发现 `funct`、`functi` 或 `functio`。

</aside>

```lox
fun printSum(a, b) {
  print a + b;
}
```

<!--
Now's a good time to clarify some <span name="define">terminology</span>. Some
people throw around "parameter" and "argument" like they are interchangeable
and, to many, they are. We're going to spend a lot of time splitting the finest
of downy hairs around semantics, so let's sharpen our words. From here on out:
-->
现在是个好时机，来厘清一些<span name="define">术语</span>。有人把“参数”（parameter）和“实参”（argument）混为一谈，对许多人来说，它们确实可以互换。我们将在语义上把最细软的绒毛一根根分开，所以先把用词磨利。从此处起：

<!--
*   An **argument** is an actual value you pass to a function when you call it.
    So a function *call* has an *argument* list. Sometimes you hear **actual
    parameter** used for these.

*   A **parameter** is a variable that holds the value of the argument inside
    the body of the function. Thus, a function *declaration* has a *parameter*
    list. Others call these **formal parameters** or simply **formals**.
-->
*   **实参**（argument）是调用函数时传入的实际值。因此函数*调用*有*实参*列表。有时人们也称它们为**实际参数**（actual parameter）。

*   **形参**（parameter）是函数体内保存实参值的变量。因此函数*声明*有*形参*列表。也有人称它们为**形式参数**（formal parameters），或简称 formals。

<aside name="define">

<!--
Speaking of terminology, some statically typed languages like C make a
distinction between *declaring* a function and *defining* it. A declaration
binds the function's type to its name so that calls can be type-checked but does
not provide a body. A definition declares the function and also fills in the
body so that the function can be compiled.

Since Lox is dynamically typed, this distinction isn't meaningful. A function
declaration fully specifies the function including its body.
-->
说到术语，C 等某些静态类型语言区分*声明*函数与*定义*函数。声明把函数的类型绑定到其名，以便对调用做类型检查，但不提供函数体。定义则声明函数并填入函数体，使函数可以被编译。

Lox 是动态类型的，这种区分没有意义。函数声明完整指定函数，包括其函数体。

</aside>

<!--
The body of a function is always a block. Inside it, you can return a value
using a `return` statement.
-->
函数的函数体总是一个块。在块内，你可以用 `return` 语句返回值。

```lox
fun returnSum(a, b) {
  return a + b;
}
```

<!--
If execution reaches the end of the block without hitting a `return`, it
<span name="sneaky">implicitly</span> returns `nil`.
-->
若执行到达块末尾而未遇到 `return`，则<span name="sneaky">隐式</span>返回 `nil`。

<aside name="sneaky">

<!--
See, I told you `nil` would sneak in when we weren't looking.
-->
看，我说过吧，`nil` 会在我们没留神的时候悄悄溜进来。

</aside>

<!--
### Closures
-->
### 闭包

<!--
Functions are *first class* in Lox, which just means they are real values that
you can get a reference to, store in variables, pass around, etc. This works:
-->
Lox 中的函数是*一等公民*（first class），意思是它们是真正的值，你可以获取其引用、存入变量、传来传去，等等。下面这样写是成立的：

```lox
fun addPair(a, b) {
  return a + b;
}

fun identity(a) {
  return a;
}

print identity(addPair)(1, 2); // Prints "3".
```

<!--
Since function declarations are statements, you can declare local functions
inside another function.
-->
函数声明是语句，因此你可以在另一个函数内部声明局部函数。

```lox
fun outerFunction() {
  fun localFunction() {
    print "I'm local!";
  }

  localFunction();
}
```

<!--
If you combine local functions, first-class functions, and block scope, you run
into this interesting situation:
-->
若把局部函数、一等函数和块作用域结合起来，就会遇到这种有趣的情形：

```lox
fun returnFunction() {
  var outside = "outside";

  fun inner() {
    print outside;
  }

  return inner;
}

var fn = returnFunction();
fn();
```

<!--
Here, `inner()` accesses a local variable declared outside of its body in the
surrounding function. Is this kosher? Now that lots of languages have borrowed
this feature from Lisp, you probably know the answer is yes.
-->
此处 `inner()` 访问了外围函数中、在其函数体之外声明的局部变量。这合规矩吗？如今许多语言都从 Lisp 借来了这一特性，你大概知道答案是：合规矩。

<!--
For that to work, `inner()` has to "hold on" to references to any surrounding
variables that it uses so that they stay around even after the outer function
has returned. We call functions that do this <span
name="closure">**closures**</span>. These days, the term is often used for *any*
first-class function, though it's sort of a misnomer if the function doesn't
happen to close over any variables.
-->
为此，`inner()` 必须“抓住”它所使用的外围变量的引用，使这些变量在外层函数返回之后仍然存在。我们把这样做的函数称为<span name="closure">**闭包**</span>（closures）。如今这个词常被用来指*任何*一等函数，但若函数并未捕获任何变量，这称呼就有点名不副实了。

<aside name="closure">

<!--
Peter J. Landin coined the term "closure". Yes, he invented damn near half the
terms in programming languages. Most of them came out of one incredible paper,
"[The Next 700 Programming Languages][svh]".
-->
Peter J. Landin 创造了“闭包”一词。没错，程序设计语言里差不多一半的术语都是他发明的。其中大多数出自一篇惊人的论文：[The Next 700 Programming Languages][svh]。

[svh]: https://homepages.inf.ed.ac.uk/wadler/papers/papers-we-love/landin-next-700.pdf

<!--
In order to implement these kind of functions, you need to create a data
structure that bundles together the function's code and the surrounding
variables it needs. He called this a "closure" because it *closes over* and
holds on to the variables it needs.
-->
要实现这类函数，你需要创建一个数据结构，把函数的代码与其所需的外围变量捆绑在一起。他称之为“闭包”，因为它*封闭并捕获*（closes over）所需的变量。

</aside>

<!--
As you can imagine, implementing these adds some complexity because we can no
longer assume variable scope works strictly like a stack where local variables
evaporate the moment the function returns. We're going to have a fun time
learning how to make these work correctly and efficiently.
-->
可想而知，实现它们会增加一些复杂度，因为我们不能再假设变量作用域严格像栈那样工作——局部变量在函数返回的瞬间便烟消云散。学习如何让它们正确而高效地运转，会是一段有趣的旅程。

<!--
## Classes
-->
## 类

<!--
Since Lox has dynamic typing, lexical (roughly, "block") scope, and closures,
it's about halfway to being a functional language. But as you'll see, it's
*also* about halfway to being an object-oriented language. Both paradigms have a
lot going for them, so I thought it was worth covering some of each.
-->
Lox 拥有动态类型、词法（大致即“块”）作用域和闭包，已经半只脚踏进了函数式语言的门槛。但正如你将看到的，它也*同样*半只脚踏进了面向对象语言的门槛。两种范式都各有长处，所以我觉得值得各取一些来介绍。

<!--
Since classes have come under fire for not living up to their hype, let me first
explain why I put them into Lox and this book. There are really two questions:
-->
既然类因未能兑现其宣传而饱受诟病，让我先解释为何仍把它们放进 Lox 和本书。其实有两个问题：

<!--
### Why might any language want to be object oriented?
-->
### 为何一门语言会想要面向对象？

<!--
Now that object-oriented languages like Java have sold out and only play arena
shows, it's not cool to like them anymore. Why would anyone make a *new*
language with objects? Isn't that like releasing music on 8-track?
-->
如今像 Java 这样的面向对象语言早已“卖身”巡回，只在体育馆开演唱会了，再喜欢它们就不酷了。为何还有人要造一门带对象的*新*语言？这不就像在八轨磁带上发行音乐吗？

<!--
It is true that the "all inheritance all the time" binge of the '90s produced
some monstrous class hierarchies, but **object-oriented programming** (**OOP**)
is still pretty rad. Billions of lines of successful code have been written in
OOP languages, shipping millions of apps to happy users. Likely a majority of
working programmers today are using an object-oriented language. They can't all
be *that* wrong.
-->
诚然，九十年代“万物皆继承”的狂热催生了一些骇人的类层次结构，但**面向对象编程**（**OOP**）依然相当棒。数十亿行成功的代码用 OOP 语言写成，数百万应用送达满意用户手中。当今在业程序员里，很可能多数都在使用面向对象语言。他们不可能*全都*错得那么离谱。

<!--
In particular, for a dynamically typed language, objects are pretty handy. We
need *some* way of defining compound data types to bundle blobs of stuff
together.
-->
尤其对于动态类型语言而言，对象相当实用。我们需要*某种*方式定义复合数据类型，把一堆东西捆在一起。

<!--
If we can also hang methods off of those, then we avoid the need to prefix all
of our functions with the name of the data type they operate on to avoid
colliding with similar functions for different types. In, say, Racket, you end
up having to name your functions like `hash-copy` (to copy a hash table) and
`vector-copy` (to copy a vector) so that they don't step on each other. Methods
are scoped to the object, so that problem goes away.
-->
若还能把方法挂在对象上，就不必给所有函数加上它们所操作的数据类型名作为前缀，以免与针对不同类型的类似函数冲突。比如在 Racket 里，你往往得把函数命名为 `hash-copy`（复制哈希表）和 `vector-copy`（复制向量），免得它们互相踩踏。方法的作用域限定在对象上，这个问题便消失了。

<!--
### Why is Lox object oriented?
-->
### 为何 Lox 是面向对象的？

<!--
I could claim objects are groovy but still out of scope for the book. Most
programming language books, especially ones that try to implement a whole
language, leave objects out. To me, that means the topic isn't well covered.
With such a widespread paradigm, that omission makes me sad.
-->
我本可以声称对象很酷，但仍超出本书范围。大多数程序语言书，尤其是试图实现一整门语言的那种，都把对象略去了。对我而言，这意味着该主题缺乏良好覆盖。如此广泛的范式被遗漏，让我有些难过。

<!--
Given how many of us spend all day *using* OOP languages, it seems like the
world could use a little documentation on how to *make* one. As you'll see, it
turns out to be pretty interesting. Not as hard as you might fear, but not as
simple as you might presume, either.
-->
鉴于我们中有许多人整天*使用* OOP 语言，世界似乎需要一点关于如何*造出*一门这样的语言的文档。如你将见，它其实相当有趣——不像你担心的那么难，也不像你以为的那么简单。

<!--
### Classes or prototypes
-->
### 类还是原型？

<!--
When it comes to objects, there are actually two approaches to them, [classes][]
and [prototypes][]. Classes came first, and are more common thanks to C++, Java,
C#, and friends. Prototypes were a virtually forgotten offshoot until JavaScript
accidentally took over the world.
-->
说到对象，其实有两种思路：[类][classes]和[原型][prototypes]。类出现得更早，因 C++、Java、C# 及其同族而更常见。原型曾是几乎被遗忘的分支，直到 JavaScript 意外统治了世界。

[classes]: https://en.wikipedia.org/wiki/Class-based_programming
[prototypes]: https://en.wikipedia.org/wiki/Prototype-based_programming

<!--
In class-based languages, there are two core concepts: instances and classes.
Instances store the state for each object and have a reference to the instance's
class. Classes contain the methods and inheritance chain. To call a method on an
instance, there is always a level of indirection. You <span name="dispatch">look
up the instance's class and then you find the method *there*:
-->
在基于类的语言中，有两个核心概念：实例和类。实例存储每个对象的状态，并持有指向该实例所属类的引用。类包含方法与继承链。在实例上调用方法，总有一层间接性：你<span name="dispatch">查找</span>实例的类，然后*在那里*找到方法：

<aside name="dispatch">

<!--
In a statically typed language like C++, method lookup typically happens at
compile time based on the *static* type of the instance, giving you **static
dispatch**. In contrast, **dynamic dispatch** looks up the class of the actual
instance object at runtime. This is how virtual methods in statically typed
languages and all methods in a dynamically typed language like Lox work.
-->
在 C++ 等静态类型语言中，方法查找通常基于实例的*静态*类型在编译期完成，即**静态分派**（static dispatch）。相比之下，**动态分派**（dynamic dispatch）在运行时查找实际实例对象的类。静态类型语言中的虚方法，以及 Lox 这类动态类型语言中的所有方法，都是这样工作的。

</aside>

<img src="image/the-lox-language/class-lookup.png" alt="How fields and methods are looked up on classes and instances" />

<!--
Prototype-based languages <span name="blurry">merge</span> these two concepts.
There are only objects -- no classes -- and each individual object may contain
state and methods. Objects can directly inherit from each other (or "delegate
to" in prototypal lingo):
-->
基于原型的语言<span name="blurry">合并</span>了这两个概念。只有对象——没有类——每个对象自身可包含状态和方法。对象可以直接彼此继承（在原型术语里叫“委托给”）：

<aside name="blurry">

<!--
In practice the line between class-based and prototype-based languages blurs.
JavaScript's "constructor function" notion [pushes you pretty hard][js new]
towards defining class-like objects. Meanwhile, class-based Ruby is perfectly
happy to let you attach methods to individual instances.
-->
实践中，基于类与基于原型的语言之间的界线会模糊。JavaScript 的“构造函数”概念[相当强力地推着你][js new]去定义类似类的对象。与此同时，基于类的 Ruby 也乐于让你给单个实例挂载方法。

[js new]: http://gameprogrammingpatterns.com/prototype.html#what-about-javascript

</aside>

<img src="image/the-lox-language/prototype-lookup.png" alt="How fields and methods are looked up in a prototypal system" />

<!--
This means that in some ways prototypal languages are more fundamental than
classes. They are really neat to implement because they're *so* simple. Also,
they can express lots of unusual patterns that classes steer you away from.
-->
这意味着在某些方面，原型语言比类更为根本。实现起来非常清爽，因为它们*极其*简单。它们也能表达许多类会把你引开的不寻常模式。

<!--
But I've looked at a *lot* of code written in prototypal languages -- including
[some of my own devising][finch]. Do you know what people generally do with all
of the power and flexibility of prototypes? ...They use them to reinvent
classes.
-->
但我看过*大量*用原型语言写的代码——包括[我自己设计的][finch]一些。你知道人们通常拿原型的全部力量与灵活性做什么吗？……他们用它们重新发明类。

[finch]: http://finch.stuffwithstuff.com/

<!--
I don't know *why* that is, but people naturally seem to prefer a class-based
(Classic? Classy?) style. Prototypes *are* simpler in the language, but they
seem to accomplish that only by <span name="waterbed">pushing</span> the
complexity onto the user. So, for Lox, we'll save our users the trouble and bake
classes right in.
-->
我不知道*为何*如此，但人们似乎天然偏好基于类的（Classic？Classy？）风格。原型在语言层面*确实*更简单，但似乎只是通过把<span name="waterbed">复杂度</span>推给用户来达成。所以，为 Lox，我们替用户省去麻烦，直接把类烘焙进去。

<aside name="waterbed">

<!--
Larry Wall, Perl's inventor/prophet calls this the "[waterbed theory][]". Some
complexity is essential and cannot be eliminated. If you push it down in one
place, it swells up in another.
-->
Larry Wall，Perl 的发明者/先知，称之为“[水床理论][waterbed theory]”。有些复杂度是本质的，无法消除。你若在一处压下去，别处就会鼓起来。

[waterbed theory]: http://wiki.c2.com/?WaterbedTheory

<!--
Prototypal languages don't so much *eliminate* the complexity of classes as they
do make the *user* take that complexity by building their own class-like
metaprogramming libraries.
-->
原型语言与其说是*消除*类的复杂度，不如说是让*用户*通过构建自己的类式元编程库来承担那复杂度。

</aside>

<!--
### Classes in Lox
-->
### Lox 中的类

<!--
Enough rationale, let's see what we actually have. Classes encompass a
constellation of features in most languages. For Lox, I've selected what I think
are the brightest stars. You declare a class and its methods like so:
-->
道理够多了，看看我们实际有什么。在大多数语言里，类囊括一簇特性。为 Lox，我选了我认为最亮的几颗星。你可以这样声明类及其方法：

```lox
class Breakfast {
  cook() {
    print "Eggs a-fryin'!";
  }

  serve(who) {
    print "Enjoy your breakfast, " + who + ".";
  }
}
```

<!--
The body of a class contains its methods. They look like function declarations
but without the `fun` <span name="method">keyword</span>. When the class
declaration is executed, Lox creates a class object and stores that in a
variable named after the class. Just like functions, classes are first class in
Lox.
-->
类的函数体包含其方法。它们看起来像函数声明，但没有 `fun` <span name="method">关键字</span>。类声明执行时，Lox 创建类对象，并存入与类同名的变量。与函数一样，类在 Lox 中也是一等公民。

<aside name="method">

<!--
They are still just as fun, though.
-->
不过，它们照样有趣。

</aside>

```lox
// Store it in variables.
var someVariable = Breakfast;

// Pass it to functions.
someFunction(Breakfast);
```

<!--
Next, we need a way to create instances. We could add some sort of `new`
keyword, but to keep things simple, in Lox the class itself is a factory
function for instances. Call a class like a function, and it produces a new
instance of itself.
-->
接下来，我们需要创建实例的方式。本可以添加某种 `new` 关键字，但为保持简单，在 Lox 中类本身就是实例的工厂函数。像调用函数一样调用类，它便产生自身的新实例。

```lox
var breakfast = Breakfast();
print breakfast; // "Breakfast instance".
```

<!--
### Instantiation and initialization
-->
### 实例化与初始化

<!--
Classes that only have behavior aren't super useful. The idea behind
object-oriented programming is encapsulating behavior *and state* together. To
do that, you need fields. Lox, like other dynamically typed languages, lets you
freely add properties onto objects.
-->
只有行为、没有状态的类不太实用。面向对象编程的理念是把行为*与状态*封装在一起。为此你需要字段。Lox 与其他动态类型语言一样，允许你自由给对象添加属性。

```lox
breakfast.meat = "sausage";
breakfast.bread = "sourdough";
```

<!--
Assigning to a field creates it if it doesn't already exist.
-->
给字段赋值时，若字段尚不存在，便会创建它。

<!--
If you want to access a field or method on the current object from within a
method, you use good old `this`.
-->
若要在方法内访问当前对象的字段或方法，使用老派的 `this`。

```lox
class Breakfast {
  serve(who) {
    print "Enjoy your " + this.meat + " and " +
        this.bread + ", " + who + ".";
  }

  // ...
}
```

<!--
Part of encapsulating data within an object is ensuring the object is in a valid
state when it's created. To do that, you can define an initializer. If your
class has a method named `init()`, it is called automatically when the object is
constructed. Any parameters passed to the class are forwarded to its
initializer.
-->
在对象内封装数据的一部分，是确保对象创建时处于有效状态。为此可以定义初始化器。若类有名为 `init()` 的方法，对象构造时会自动调用。传给类的任何参数都会转发给其初始化器。

```lox
class Breakfast {
  init(meat, bread) {
    this.meat = meat;
    this.bread = bread;
  }

  // ...
}

var baconAndToast = Breakfast("bacon", "toast");
baconAndToast.serve("Dear Reader");
// "Enjoy your bacon and toast, Dear Reader."
```

<!--
### Inheritance
-->
### 继承

<!--
Every object-oriented language lets you not only define methods, but reuse them
across multiple classes or objects. For that, Lox supports single inheritance.
When you declare a class, you can specify a class that it inherits from using a less-than
<span name="less">(`<`)</span> operator.
-->
每种面向对象语言都不仅让你定义方法，还能在多个类或对象间复用它们。为此，Lox 支持单继承。声明类时，可用小于号 <span name="less">（`<`）</span> 运算符指定它继承的类。

```lox
class Brunch < Breakfast {
  drink() {
    print "How about a Bloody Mary?";
  }
}
```

<aside name="less">

<!--
Why the `<` operator? I didn't feel like introducing a new keyword like
`extends`. Lox doesn't use `:` for anything else so I didn't want to reserve
that either. Instead, I took a page from Ruby and used `<`.
-->
为何用 `<` 运算符？我不想引入 `extends` 这类新关键字。Lox 别处也不用 `:`，我也不想保留它。于是，我向 Ruby 取经，用了 `<`。

<!--
If you know any type theory, you'll notice it's not a *totally* arbitrary
choice. Every instance of a subclass is an instance of its superclass too, but
there may be instances of the superclass that are not instances of the subclass.
That means, in the universe of objects, the set of subclass objects is smaller
than the superclass's set, though type nerds usually use `<:` for that relation.
-->
若你懂一点类型论，会注意到这并非*完全*随意的选择。子类的每个实例也是其超类的实例，但超类可能有不是子类实例的实例。也就是说，在对象宇宙中，子类对象集合小于超类集合——尽管类型极客通常用 `<:` 表示这种关系。

</aside>

<!--
Here, Brunch is the **derived class** or **subclass**, and Breakfast is the
**base class** or **superclass**.
-->
此处 Brunch 是**派生类**（derived class）或**子类**（subclass），Breakfast 是**基类**（base class）或**超类**（superclass）。

<!--
Every method defined in the superclass is also available to its subclasses.
-->
超类中定义的每个方法，其子类也可使用。

```lox
var benedict = Brunch("ham", "English muffin");
benedict.serve("Noble Reader");
```

<!--
Even the `init()` method gets <span name="init">inherited</span>. In practice,
the subclass usually wants to define its own `init()` method too. But the
original one also needs to be called so that the superclass can maintain its
state. We need some way to call a method on our own *instance* without hitting
our own *methods*.
-->
连 `init()` 方法也会<span name="init">被继承</span>。实践中，子类通常也想定义自己的 `init()` 方法。但原版的也需要被调用，以便超类维持其状态。我们需要某种方式，在自己的*实例*上调用方法，而不触发自己的*方法*。

<aside name="init">

<!--
Lox is different from C++, Java, and C#, which do not inherit constructors, but
similar to Smalltalk and Ruby, which do.
-->
Lox 与 C++、Java、C# 不同——它们不继承构造函数——但类似 Smalltalk 和 Ruby，它们会继承。

</aside>

<!--
As in Java, you use `super` for that.
-->
与 Java 一样，对此你使用 `super`。

```lox
class Brunch < Breakfast {
  init(meat, bread, drink) {
    super.init(meat, bread);
    this.drink = drink;
  }
}
```

<!--
That's about it for object orientation. I tried to keep the feature set minimal.
The structure of the book did force one compromise. Lox is not a *pure*
object-oriented language. In a true OOP language every object is an instance of
a class, even primitive values like numbers and Booleans.
-->
面向对象就这些了。我尽量保持特性集最小。书的结构迫使我作出一项妥协：Lox 不是*纯*面向对象语言。在真正的 OOP 语言里，每个对象都是类的实例，连数字和布尔这类原始值也不例外。

<!--
Because we don't implement classes until well after we start working with the
built-in types, that would have been hard. So values of primitive types aren't
real objects in the sense of being instances of classes. They don't have methods
or properties. If I were trying to make Lox a real language for real users, I
would fix that.
-->
因为我们直到深入内置类型之后很久才实现类，那样做会很难。所以原始类型的值，在“是类的实例”意义上并非真正对象。它们没有方法或属性。若我试图把 Lox 做成给真实用户用的真实语言，我会修正这一点。

<!--
## The Standard Library
-->
## 标准库

<!--
We're almost done. That's the whole language, so all that's left is the "core"
or "standard" library -- the set of functionality that is implemented directly
in the interpreter and that all user-defined behavior is built on top of.
-->
我们快完成了。语言本体就是这些，剩下的只有“核心”或“标准”库——直接在解释器中实现、所有用户定义行为都建立其上的那套功能。

<!--
This is the saddest part of Lox. Its standard library goes beyond minimalism and
veers close to outright nihilism. For the sample code in the book, we only need
to demonstrate that code is running and doing what it's supposed to do. For
that, we already have the built-in `print` statement.
-->
这是 Lox 最叫人难过的一部分。它的标准库超越了极简主义，几乎滑向彻底的虚无主义。对书中的示例代码，我们只需证明代码在运行、并按预期工作。为此，我们已有内建的 `print` 语句。

<!--
Later, when we start optimizing, we'll write some benchmarks and see how long it
takes to execute code. That means we need to track time, so we'll define one
built-in function, `clock()`, that returns the number of seconds since the
program started.
-->
稍后，当我们开始优化时，会写一些基准测试，看执行代码要多久。这意味着需要追踪时间，所以会定义一个内建函数 `clock()`，返回程序启动以来的秒数。

<!--
And... that's it. I know, right? It's embarrassing.
-->
然后……就这些了。我知道，对吧？挺丢人的。

<!--
If you wanted to turn Lox into an actual useful language, the very first thing
you should do is flesh this out. String manipulation, trigonometric functions,
file I/O, networking, heck, even *reading input from the user* would help. But we
don't need any of that for this book, and adding it wouldn't teach you anything
interesting, so I've left it out.
-->
若你想把 Lox 变成真正有用的语言，第一件该做的事就是充实标准库。字符串处理、三角函数、文件 I/O、网络，天哪，哪怕*从用户读取输入*都会有帮助。但本书不需要这些，加上它们也教不了你什么有趣的东西，所以我略去了。

<!--
Don't worry, we'll have plenty of exciting stuff in the language itself to keep
us busy.
-->
别担心，语言本身会有足够多令人兴奋的东西让我们忙个不停。

<div class="challenges">

## 挑战

<!--
1. Write some sample Lox programs and run them (you can use the implementations
   of Lox in [my repository][repo]). Try to come up with edge case behavior I
   didn't specify here. Does it do what you expect? Why or why not?
-->
1. 写一些 Lox 示例程序并运行（可使用[我的仓库][repo]里的 Lox 实现）。试着想出我在此未指定的边界情形行为。结果是否符合你的预期？为什么？

<!--
2. This informal introduction leaves a *lot* unspecified. List several open
   questions you have about the language's syntax and semantics. What do you
   think the answers should be?
-->
2. 这份非正式介绍留下了*大量*未说明之处。列出你对语言语法与语义的几条开放问题。你认为答案应该是什么？

<!--
3. Lox is a pretty tiny language. What features do you think it is missing that
   would make it annoying to use for real programs? (Aside from the standard
   library, of course.)
-->
3. Lox 是一门相当小的语言。你认为它缺少哪些特性，会让写真实程序变得烦人？（标准库除外，当然。）

</div>

<div class="design-note">

## 设计笔记：表达式与语句

<!--
Lox has both expressions and statements. Some languages omit the latter.
Instead, they treat declarations and control flow constructs as expressions too.
These "everything is an expression" languages tend to have functional pedigrees
and include most Lisps, SML, Haskell, Ruby, and CoffeeScript.
-->
Lox 既有表达式也有语句。有些语言省略后者，转而把声明和控制流结构也当作表达式。这类“一切皆表达式”的语言往往有函数式血统，包括大多数 Lisp、SML、Haskell、Ruby 和 CoffeeScript。

<!--
To do that, for each "statement-like" construct in the language, you need to
decide what value it evaluates to. Some of those are easy:
-->
为此，对语言中每种“像语句”的结构，你都需要决定它求值为什么。有些很简单：

<!--
*   An `if` expression evaluates to the result of whichever branch is chosen.
    Likewise, a `switch` or other multi-way branch evaluates to whichever case
    is picked.

*   A variable declaration evaluates to the value of the variable.

*   A block evaluates to the result of the last expression in the sequence.
-->
*   `if` 表达式求值为所选分支的结果。同样，`switch` 或其他多路分支求值为所选 case 的结果。

*   变量声明求值为变量的值。

*   块求值为序列中最后一个表达式的结果。

<!--
Some get a little stranger. What should a loop evaluate to? A `while` loop in
CoffeeScript evaluates to an array containing each element that the body
evaluated to. That can be handy, or a waste of memory if you don't need the
array.
-->
有些就怪一些。循环该求值为什么？CoffeeScript 中的 `while` 循环求值为一个数组，包含循环体每次求值的结果。有时颇为便利，若你不需要数组则是浪费内存。

<!--
You also have to decide how these statement-like expressions compose with other
expressions -- you have to fit them into the grammar's precedence table. For
example, Ruby allows:
-->
你还必须决定这些像语句的表达式如何与其他表达式组合——要把它们纳入语法的优先级表。例如，Ruby 允许：

```ruby
puts 1 + if true then 2 else 3 end + 4
```

<!--
Is this what you'd expect? Is it what your *users* expect? How does this affect
how you design the syntax for your "statements"? Note that Ruby has an explicit
`end` to tell when the `if` expression is complete. Without it, the `+ 4` would
likely be parsed as part of the `else` clause.
-->
这是你预期的吗？是*用户*预期的吗？这如何影响你设计“语句”的语法？注意 Ruby 有显式的 `end` 来标明 `if` 表达式结束。没有它，`+ 4` 很可能被解析为 `else` 子句的一部分。

<!--
Turning every statement into an expression forces you to answer a few hairy
questions like that. In return, you eliminate some redundancy. C has both blocks
for sequencing statements, and the comma operator for sequencing expressions. It
has both the `if` statement and the `?:` conditional operator. If everything was
an expression in C, you could unify each of those.
-->
把每条语句都变成表达式，迫使你回答若干棘手问题。回报是消除一些冗余。C 既有用于语句序列的块，也有用于表达式序列的逗号运算符；既有 `if` 语句，也有 `?:` 条件运算符。若 C 中一切皆表达式，你可以统一它们。

<!--
Languages that do away with statements usually also feature **implicit returns**
-- a function automatically returns whatever value its body evaluates to without
need for some explicit `return` syntax. For small functions and methods, this is
really handy. In fact, many languages that do have statements have added syntax
like `=>` to be able to define functions whose body is the result of evaluating
a single expression.
-->
取消语句的语言通常还有**隐式返回**——函数自动返回其函数体求值的结果，无需显式 `return` 语法。对小函数和方法，这非常便利。事实上，许多保留语句的语言也添加了 `=>` 等语法，以定义函数体为单个表达式求值结果的函数。

<!--
But making *all* functions work that way can be a little strange. If you aren't
careful, your function will leak a return value even if you only intend it to
produce a side effect. In practice, though, users of these languages don't find
it to be a problem.
-->
但让*所有*函数都这样工作会有点怪。若不小心，函数会泄漏返回值，即便你只想产生副作用。实践中，这些语言的用户并不觉得这是问题。

<!--
For Lox, I gave it statements for prosaic reasons. I picked a C-like syntax for
familiarity's sake, and trying to take the existing C statement syntax and
interpret it like expressions gets weird pretty fast.
-->
对 Lox，我出于平凡理由保留了语句。我为熟悉感选择了类 C 语法，而试图把现有 C 语句语法当作表达式来解释，很快就会变得古怪。

</div>
