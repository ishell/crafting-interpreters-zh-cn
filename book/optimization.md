# 优化

<!--
> The evening's the best part of the day. You've done your day's work. Now you
> can put your feet up and enjoy it.
>
> <cite>Kazuo Ishiguro, <em>The Remains of the Day</em></cite>
-->
> 傍晚是一天里最好的时光。白天的活干完了。现在可以搁起脚来好好享受。
>
> <cite>石黑一雄，<em>《长日将尽》</em></cite>

<!--
If I still lived in New Orleans, I'd call this chapter a *lagniappe*, a little
something extra given for free to a customer. You've got a whole book and a
complete virtual machine already, but I want you to have some more fun hacking
on clox. This time, we're going for pure performance. We'll apply two very
different optimizations to our virtual machine.  In the process, you'll get a
feel for measuring and improving the performance of a language implementation --
or any program, really.
-->
若我还住在新奥尔良，我会把这一章叫做 *lagniappe*（新奥尔良的“额外赠品”）——送给顾客的一点免费小礼物。你已经拥有一整本书、一台完整的虚拟机，可我还想让你在 clox 上多玩一会儿。这一次，我们冲着纯粹的性能去。我们会给虚拟机施加两种截然不同的优化。过程中，你会摸到测量并改进一门语言实现——其实是任何程序——性能的那种手感。

<!--
-- Measuring Performance
-->
## 测量性能

<!--
**Optimization** means taking a working application and improving its
performance. An optimized program does the same thing, it just takes less
resources to do so. The resource we usually think of when optimizing is runtime
speed, but it can also be important to reduce memory usage, startup time,
persistent storage size, or network bandwidth. All physical resources have some
cost -- even if the cost is mostly in wasted human time -- so optimization work
often pays off.
-->
**优化**意味着拿一个已经能工作的应用，改进它的性能。优化后的程序做的事一样，只是耗费更少资源。我们通常想到的资源是运行速度，但降低内存占用、启动时间、持久存储体积或网络带宽同样重要。一切物理资源都有代价——即便代价多半是浪费的人时——所以优化工作往往划得来。

<!--
There was a time in the early days of computing that a skilled programmer could
hold the entire hardware architecture and compiler pipeline in their head and
understand a program's performance just by thinking real hard. Those days are
long gone, separated from the present by microcode, cache lines, branch
prediction, deep compiler pipelines, and mammoth instruction sets. We like to
pretend C is a "low-level" language, but the stack of technology between
```c
printf("Hello, world!");
```

and a greeting appearing on screen is now perilously tall.
-->
计算早期有那么一段时光：熟练的程序员能把整台硬件架构与编译器流水线装进脑子里，光靠使劲想就能理解程序的性能。那些日子早已远去，中间隔着微码、缓存行、分支预测、深邃的编译器流水线，以及庞大的指令集。我们喜欢假装 C 是“低级”语言，可从 `printf("Hello, world!");` 到屏幕上出现问候，技术栈如今已高得吓人。

<!--
Optimization today is an empirical science. Our program is a border collie
sprinting through the hardware's obstacle course. If we want her to reach the
end faster, we can't just sit and ruminate on canine physiology until
enlightenment strikes. Instead, we need to *observe* her performance, see where
she stumbles, and then find faster paths for her to take.
-->
今天的优化是一门实证科学。我们的程序是一只边境牧羊犬，在硬件的障碍赛道上飞奔。若想让她更快到达终点，不能干坐着琢磨犬类生理学直到顿悟降临。相反，我们需要*观察*她的表现，看她在何处绊脚，再为她找到更快的路径。

<!--
Much like agility training is particular to one dog and one obstacle course, we
can't assume that our virtual machine optimizations will make *all* Lox programs
run faster on *all* hardware. Different Lox programs stress different areas of
the VM, and different architectures have their own strengths and weaknesses.
-->
正如敏捷训练针对的是某一只狗、某一条障碍赛道，我们也不能假定虚拟机优化会让*所有* Lox 程序在*所有*硬件上都更快。不同的 Lox 程序压迫虚拟机的不同区域，不同架构也各有长短。

<!--
-- Benchmarks
-->
### 基准测试

<!--
When we add new functionality, we validate correctness by writing tests -- Lox
programs that use a feature and validate the VM's behavior. Tests pin down
semantics and ensure we don't break existing features when we add new ones. We
have similar needs when it comes to performance:
-->
添加新功能时，我们靠写测试来验证正确性——那些使用某项特性并校验虚拟机行为的 Lox 程序。测试钉死语义，确保加新功能时不弄坏已有特性。谈到性能，我们也有类似需求：

<!--
1.  How do we validate that an optimization *does* improve performance, and by
    how much?

2.  How do we ensure that other unrelated changes don't *regress* performance?
-->
1.  如何验证一项优化*确实*改进了性能，以及改进了多少？

2.  如何确保其他无关改动不会让性能*回退*？

<!--
The Lox programs we write to accomplish those goals are **benchmarks**. These
are carefully crafted programs that stress some part of the language
implementation. They measure not *what* the program does, but how <span
name="much">*long*</span> it takes to do it.
-->
为实现这些目标而写的 Lox 程序，就是**基准测试**。它们是精心打造的程序，专门压迫语言实现的某一部分。它们衡量的不是程序做了*什么*，而是做这件事花了多<span
name="much">*久*</span>。

<aside name="much">

<!--
Most benchmarks measure running time. But, of course, you'll eventually find
yourself needing to write benchmarks that measure memory allocation, how much
time is spent in the garbage collector, startup time, etc.
-->
多数基准测试衡量运行时间。但当然，你最终也会需要写衡量内存分配、垃圾回收器耗时、启动时间等等的基准。

</aside>

<!--
By measuring the performance of a benchmark before and after a change, you can
see what your change does. When you land an optimization, all of the tests
should behave exactly the same as they did before, but hopefully the benchmarks
run faster.
-->
在改动前后测量同一基准的性能，就能看见改动带来了什么。落地一项优化时，所有测试的行为应与之前完全一致，但愿基准跑得更快。

<!--
Once you have an entire <span name="js">*suite*</span> of benchmarks, you can
measure not just *that* an optimization changes performance, but on which
*kinds* of code. Often you'll find that some benchmarks get faster while others
get slower. Then you have to make hard decisions about what kinds of code your
language implementation optimizes for.
-->
一旦你有一整套<span name="js">*基准套件*</span>，就能衡量的不只是优化*是否*改变了性能，还有它作用于*哪类*代码。你常会发现有些基准变快、有些变慢。于是你得做出艰难决定：你的语言实现要为哪类代码优化。

<!--
The suite of benchmarks you choose to write is a key part of that decision. In
the same way that your tests encode your choices around what correct behavior
looks like, your benchmarks are the embodiment of your priorities when it comes
to performance. They will guide which optimizations you implement, so choose
your benchmarks carefully, and don't forget to periodically reflect on whether
they are helping you reach your larger goals.
-->
你选择编写的那套基准，是这一决策的关键部分。正如测试编码了你对“正确行为”的选择，基准则是你在性能优先级上的化身。它们会引导你实现哪些优化，所以要谨慎挑选基准，也别忘了定期反思：它们是否在帮你抵达更大的目标。

<aside name="js">

<!--
In the early proliferation of JavaScript VMs, the first widely used benchmark
suite was SunSpider from WebKit. During the browser wars, marketing folks used
SunSpider results to claim their browser was fastest. That highly incentivized
VM hackers to optimize to those benchmarks.
-->
JavaScript 虚拟机早期井喷时，首个广泛使用的基准套件是 WebKit 的 SunSpider。浏览器大战期间，市场人员拿 SunSpider 成绩宣称自家浏览器最快。这强烈激励虚拟机黑客去为那些基准做优化。

<!--
Unfortunately, SunSpider programs often didn't match real-world JavaScript. They
were mostly microbenchmarks -- tiny toy programs that completed quickly. Those
benchmarks penalize complex just-in-time compilers that start off slower but get
*much* faster once the JIT has had enough time to optimize and re-compile hot
code paths. This put VM hackers in the unfortunate position of having to choose
between making the SunSpider numbers get better, or actually optimizing the
kinds of programs real users ran.
-->
不幸的是，SunSpider 程序往往与真实世界的 JavaScript 对不上。它们多半是微基准——很快跑完的小玩具程序。那些基准会惩罚复杂的即时编译器：起步较慢，但一旦 JIT 有足够时间优化并重编译热路径，就会变得*快得多*。这让虚拟机黑客陷入尴尬：要么把 SunSpider 数字刷好看，要么真正优化真实用户跑的那类程序。

<!--
Google's V8 team responded by sharing their Octane benchmark suite, which was
closer to real-world code at the time. Years later, as JavaScript use patterns
continued to evolve, even Octane outlived its usefulness. Expect that your
benchmarks will evolve as your language's ecosystem does.
-->
Google 的 V8 团队以分享 Octane 基准套件作为回应，它当时更接近真实世界代码。多年后，随着 JavaScript 使用模式继续演变，连 Octane 也过了有用期。可以预期，你的基准会随语言生态一同演进。

<!--
Remember, the ultimate goal is to make *user programs* faster, and benchmarks
are only a proxy for that.
-->
记住，终极目标是让*用户程序*更快，基准只是它的代理。

</aside>

<!--
Benchmarking is a subtle art. Like tests, you need to balance not overfitting to
your implementation while ensuring that the benchmark does actually tickle the
code paths that you care about. When you measure performance, you need to
compensate for variance caused by CPU throttling, caching, and other weird
hardware and operating system quirks. I won't give you a whole sermon here,
but treat benchmarking as its own skill that improves with practice.
-->
基准测试是一门微妙的艺术。像测试一样，你既要避免对实现过拟合，又要确保基准确实触碰到你关心的代码路径。测量性能时，你需要补偿 CPU 降频、缓存，以及其他古怪的硬件与操作系统怪癖带来的方差。我不会在此布道一整篇，但请把基准测试当作一门随练习而精进的独立技能。

<!--
-- Profiling
-->
### 性能分析

<!--
OK, so you've got a few benchmarks now. You want to make them go faster. Now
what? First of all, let's assume you've done all the obvious, easy work. You are
using the right algorithms and data structures -- or, at least, you aren't using
ones that are aggressively wrong. I don't consider using a hash table instead of
a linear search through a huge unsorted array "optimization" so much as "good
software engineering".
-->
好，现在你有了几个基准。你想让它们更快。然后呢？首先，假定你已做完所有显而易见的轻松活。你用的是合适的算法与数据结构——或者至少，没用那些明显错得离谱的。把哈希表换成对巨大无序数组的线性搜索，在我看来不算“优化”，更像是“合格的软件工程”。

<!--
Since the hardware is too complex to reason about our program's performance from
first principles, we have to go out into the field. That means *profiling*. A
**profiler**, if you've never used one, is a tool that runs your <span
name="program">program</span> and tracks hardware resource use as the code
executes. Simple ones show you how much time was spent in each function in your
program. Sophisticated ones log data cache misses, instruction cache misses,
branch mispredictions, memory allocations, and all sorts of other metrics.
-->
硬件太复杂，无法从第一性原理推断程序性能，我们只好下田实地考察。那就是*性能分析*。**性能分析器**（profiler），若你从未用过，是一种运行你的<span
name="program">程序</span>并在代码执行时追踪硬件资源使用的工具。简单的会告诉你程序里每个函数花了多少时间。精致的会记录数据缓存未命中、指令缓存未命中、分支误预测、内存分配，以及各种其他指标。

<aside name="program">

<!--
"Your program" here means the Lox VM itself running some *other* Lox program. We
are trying to optimize clox, not the user's Lox script. Of course, the choice of
which Lox program to load into our VM will highly affect which parts of clox get
stressed, which is why benchmarks are so important.
-->
这里的“你的程序”指的是 Lox 虚拟机本身在跑某个*别的* Lox 程序。我们要优化的是 clox，不是用户的 Lox 脚本。当然，往虚拟机里装哪段 Lox 程序，会强烈影响 clox 的哪些部分被压住——这正是基准如此重要的原因。

<!--
A profiler *won't* show us how much time is spent in each *Lox* function in the
script being run. We'd have to write our own "Lox profiler" to do that, which is
slightly out of scope for this book.
-->
性能分析器*不会*告诉我们被跑的脚本里每个*Lox* 函数花了多少时间。那得自己写一个“Lox 性能分析器”，略超出本书范围。

</aside>

<!--
There are many profilers out there for various operating systems and languages.
On whatever platform you program, it's worth getting familiar with a decent
profiler. You don't need to be a master. I have learned things within minutes of
throwing a program at a profiler that would have taken me *days* to discover on
my own through trial and error. Profilers are wonderful, magical tools.
-->
各种操作系统与语言都有许多性能分析器。无论你在哪块平台上编程，值得熟悉一款像样的分析器。不必成为大师。我把程序扔给分析器几分钟就学到的东西，自己试错可能要花上*几天*。性能分析器是美妙而神奇的工具。

<!--
-- Faster Hash Table Probing
-->
## 更快的哈希表探测

<!--
Enough pontificating, let's get some performance charts going up and to the
right. The first optimization we'll do, it turns out, is about the *tiniest*
possible change we could make to our VM.
-->
说教够了，让性能曲线往右上爬吧。我们要做的第一项优化，结果竟是对虚拟机能做的*最微小*改动之一。

<!--
When I first got the bytecode virtual machine that clox is descended from
working, I did what any self-respecting VM hacker would do. I cobbled together a
couple of benchmarks, fired up a profiler, and ran those scripts through my
interpreter. In a dynamically typed language like Lox, a large fraction of user
code is field accesses and method calls, so one of my benchmarks looked
something like this:
-->
当我第一次让 clox 的祖先——那台字节码虚拟机——跑起来时，我做了任何有自尊心的虚拟机黑客都会做的事。拼凑几个基准，拉起性能分析器，把那些脚本扔进解释器。在像 Lox 这样的动态类型语言里，用户代码很大一块是字段访问与方法调用，所以我的一个基准大致长这样：

```lox
class Zoo {
  init() {
    this.aardvark = 1;
    this.baboon   = 1;
    this.cat      = 1;
    this.donkey   = 1;
    this.elephant = 1;
    this.fox      = 1;
  }
  ant()    { return this.aardvark; }
  banana() { return this.baboon; }
  tuna()   { return this.cat; }
  hay()    { return this.donkey; }
  grass()  { return this.elephant; }
  mouse()  { return this.fox; }
}

var zoo = Zoo();
var sum = 0;
var start = clock();
while (sum < 100000000) {
  sum = sum + zoo.ant()
            + zoo.banana()
            + zoo.tuna()
            + zoo.hay()
            + zoo.grass()
            + zoo.mouse();
}

print clock() - start;
print sum;
```

<aside name="sum" class="bottom">

<!--
Another thing this benchmark is careful to do is *use* the result of the code it
executes. By calculating a rolling sum and printing the result, we ensure the VM
*must* execute all that Lox code. This is an important habit. Unlike our simple
Lox VM, many compilers do aggressive dead code elimination and are smart enough
to discard a computation whose result is never used.
-->
这个基准还小心翼翼地*使用*了所执行代码的结果。通过累计滚动求和并打印结果，我们确保虚拟机*必须*执行那些 Lox 代码。这是个重要习惯。与我们简单的 Lox 虚拟机不同，许多编译器会做激进的死代码消除，聪明到足以丢掉结果从未被用到的计算。

<!--
Many a programming language hacker has been impressed by the blazing performance
of a VM on some benchmark, only to realize that it's because the compiler
optimized the entire benchmark program away to nothing.
-->
不少程序设计语言黑客曾为某台虚拟机在基准上的狂暴性能而惊叹，随后才意识到：那是因为编译器把整个基准程序优化成了空。

</aside>

<!--
If you've never seen a benchmark before, this might seem ludicrous. *What* is
going on here? The program itself doesn't intend to <span name="sum">do</span>
anything useful. What it does do is call a bunch of methods and access a bunch
of fields since those are the parts of the language we're interested in. Fields
and methods live in hash tables, so it takes care to populate at least a <span
name="more">*few*</span> interesting keys in those tables. That is all wrapped
in a big loop to ensure our profiler has enough execution time to dig in and see
where the cycles are going.
-->
若你从未见过基准，这或许显得荒唐。*究竟*在干什么？程序本身并不打算<span name="sum">做</span>任何有用的事。它实际做的是调用一堆方法、访问一堆字段——因为那正是我们关心的语言部分。字段与方法住在哈希表里，所以它至少往那些表里塞了<span
name="more">*几个*</span>有趣的键。这一切包在一个大循环里，好让性能分析器有足够执行时间钻进去，看周期花在哪儿。

<aside name="more">

<!--
If you really want to benchmark hash table performance, you should use many
tables of different sizes. The six keys we add to each table here aren't even
enough to get over our hash table's eight-element minimum threshold. But I
didn't want to throw an enormous benchmark script at you. Feel free to add more
critters and treats if you like.
-->
若你真想基准测试哈希表性能，应当使用许多不同大小的表。我们这里往每张表加的六个键，甚至还没超过哈希表八元素的最小门槛。但我不想朝你扔一份庞大的基准脚本。喜欢的话，尽管加更多小动物和零食。

</aside>

<!--
Before I tell you what my profiler showed me, spend a minute taking a few
guesses. Where in clox's codebase do you think the VM spent most of its time? Is
there any code we've written in previous chapters that you suspect is
particularly slow?
-->
在告诉你我的分析器显示了什么之前，花一分钟猜猜。你觉得虚拟机在 clox 代码库里把大部分时间花在哪儿？先前章节写过的代码里，有没有你怀疑特别慢的？

<!--
Here's what I found: Naturally, the function with the greatest inclusive time is
`run()`. (**Inclusive time** means the total time spent in some function and all
other functions it calls -- the total time between when you enter the function
and when it returns.) Since `run()` is the main bytecode execution loop, it
drives everything.
-->
我发现的是：自然地，包容时间最大的函数是 `run()`。（**包容时间**指花在某个函数及其调用的所有其他函数上的总时间——从进入该函数到返回之间的全部时间。）既然 `run()` 是主字节码执行循环，它驱动一切。

<!--
Inside `run()`, there are small chunks of time sprinkled in various cases in the
bytecode switch for common instructions like `OP_POP`, `OP_RETURN`, and
`OP_ADD`. The big heavy instructions are `OP_GET_GLOBAL` with 17% of the
execution time, `OP_GET_PROPERTY` at 12%, and `OP_INVOKE` which takes a whopping
42% of the total running time.
-->
在 `run()` 内部，字节码 switch 里常见指令如 `OP_POP`、`OP_RETURN`、`OP_ADD` 的各个 case 上洒着小块时间。真正沉重的指令是：`OP_GET_GLOBAL` 占执行时间的 17%，`OP_GET_PROPERTY` 占 12%，而 `OP_INVOKE` 独占总运行时间的 42%，惊人。

<!--
So we've got three hotspots to optimize? Actually, no. Because it turns out
those three instructions spend almost all of their time inside calls to the same
function: `tableGet()`. That function claims a whole 72% of the execution time
(again, inclusive). Now, in a dynamically typed language, we expect to spend a
fair bit of time looking stuff up in hash tables -- it's sort of the price of
dynamism. But, still, *wow.*
-->
那么我们有三个热点要优化？其实没有。因为原来这三条指令几乎把全部时间都花在对同一个函数的调用上：`tableGet()`。该函数独占了整整 72% 的执行时间（同样是包容时间）。在动态类型语言里，我们本来就预期会花不少时间在哈希表里查找——那多少是动态性的代价。可即便如此，*哇*。

<!--
-- Slow key wrapping
-->
### 缓慢的键回绕

<!--
If you take a look at `tableGet()`, you'll see it's mostly a wrapper around a
call to `findEntry()` where the actual hash table lookup happens. To refresh
your memory, here it is in full:
-->
若你看看 `tableGet()`，会发现它多半只是包了一层对 `findEntry()` 的调用——真正的哈希表查找发生在那里。温习一下，完整如下：

```c
static Entry* findEntry(Entry* entries, int capacity,
                        ObjString* key) {
  uint32_t index = key->hash % capacity;
  Entry* tombstone = NULL;

  for (;;) {
    Entry* entry = &entries[index];
    if (entry->key == NULL) {
      if (IS_NIL(entry->value)) {
        // Empty entry.
        return tombstone != NULL ? tombstone : entry;
      } else {
        // We found a tombstone.
        if (tombstone == NULL) tombstone = entry;
      }
    } else if (entry->key == key) {
      // We found the key.
      return entry;
    }

    index = (index + 1) % capacity;
  }
}
```

<!--
When running that previous benchmark -- on my machine, at least -- the VM spends
70% of the total execution time on *one line* in this function. Any guesses as
to which one? No? It's this:
-->
跑先前那个基准时——至少在我的机器上——虚拟机把总执行时间的 70% 花在这个函数的*一行*上。猜猜是哪一行？猜不到？就是这行：

```c
  uint32_t index = key->hash % capacity;
```

<!--
That pointer dereference isn't the problem. It's the little `%`. It turns out
the modulo operator is *really* slow. Much slower than other <span
name="division">arithmetic</span> operators. Can we do something better?
-->
指针解引用不是问题。问题是那个小小的 `%`。取模运算符原来*真的*很慢。比其他<span
name="division">算术</span>运算符慢得多。我们能做得更好吗？

<aside name="division">

<!--
Pipelining makes it hard to talk about the performance of an individual CPU
instruction, but to give you a feel for things, division and modulo are about
30-50 *times* slower than addition and subtraction on x86.
-->
流水线让人很难谈论单条 CPU 指令的性能，但给你一个感觉：在 x86 上，除法与取模大约比加减慢 30–50 *倍*。

</aside>

<!--
In the general case, it's really hard to re-implement a fundamental arithmetic
operator in user code in a way that's faster than what the CPU itself can do.
After all, our C code ultimately compiles down to the CPU's own arithmetic
operations. If there were tricks we could use to go faster, the chip would
already be using them.
-->
一般情形下，在用户代码里重新实现一个基本算术运算符，并做得比 CPU 自己更快，真的很难。毕竟我们的 C 代码最终会编译成 CPU 自己的算术运算。若有能更快的技巧，芯片早就在用了。

<!--
However, we can take advantage of the fact that we know more about our problem
than the CPU does. We use modulo here to take a key string's hash code and
wrap it to fit within the bounds of the table's entry array. That array starts
out at eight elements and grows by a factor of two each time. We know -- and the
CPU and C compiler do not -- that our table's size is always a power of two.
-->
不过，我们可以利用这一点：我们对问题的了解比 CPU 更多。这里用取模，是把键字符串的哈希码回绕到表项数组的边界内。该数组从八个元素起步，每次按二倍增长。我们知道——而 CPU 与 C 编译器不知道——我们的表大小始终是二的幂。

<!--
Because we're clever bit twiddlers, we know a faster way to calculate the
remainder of a number modulo a power of two: **bit masking**. Let's say we want
to calculate 229 modulo 64. The answer is 37, which is not particularly apparent
in decimal, but is clearer when you view those numbers in binary:
-->
因为我们是聪明的位操作手，我们知道更快的办法来算一个数对二的幂取模的余数：**位掩码**。比方说我们要算 229 对 64 取模。答案是 37，十进制里不太显眼，但用二进制看那些数就清楚了：

<img src="image/optimization/mask.png" alt="The bit patterns resulting from 229 % 64 = 37 and 229 & 63 = 37." />

<!--
On the left side of the illustration, notice how the result (37) is simply the
dividend (229) with the highest two bits shaved off? Those two highest bits are
the bits at or to the left of the divisor's single 1 bit.
-->
插图左侧，注意结果（37）不过是被除数（229）剃掉最高两位？那两位最高位，正是除数那个单独的 1 位及其左侧的位。

<!--
On the right side, we get the same result by taking 229 and bitwise <span
class="small-caps">AND</span>-ing it with 63, which is one less than our
original power of two divisor. Subtracting one from a power of two gives you a
series of 1 bits. That is exactly the mask we need in order to strip out those
two leftmost bits.
-->
右侧，我们把 229 与 63 做按位 <span
class="small-caps">AND</span>，得到同样结果；63 比原来的二的幂除数少一。二的幂减一得到一串 1 位。那正是剥掉那两个最左位所需的掩码。

<!--
In other words, you can calculate a number modulo any power of two by simply
<span class="small-caps">AND</span>-ing it with that power of two minus one. I'm
not enough of a mathematician to *prove* to you that this works, but if you
think it through, it should make sense. We can replace that slow modulo operator
with a very fast decrement and bitwise <span class="small-caps">AND</span>. We
simply change the offending line of code to this:
-->
换言之，你可以对任意二的幂取模，只需与该二的幂减一做 <span class="small-caps">AND</span>。我还不够数学家到能*证明*给你看这为什么成立，但你想通了就会觉得合理。我们可以用非常快的减一与按位 <span class="small-caps">AND</span> 替换那缓慢的取模。只需把那行惹事的代码改成这样：

^code initial-index (2 before, 1 after)

<!--
CPUs love bitwise operators, so it's hard to <span name="sub">improve</span> on that. 
-->
CPU 热爱按位运算符，所以很难再<span name="sub">改进</span>什么。

<aside name="sub">

<!--
Another potential improvement is to eliminate the decrement by storing the bit
mask directly instead of the capacity. In my tests, that didn't make a
difference. Instruction pipelining makes some operations essentially free if the
CPU is bottlenecked elsewhere.
-->
另一个潜在改进是直接存位掩码而非容量，从而省掉减一。在我的测试里，这没什么差别。若 CPU 瓶颈在别处，指令流水线会让某些操作本质上免费。

</aside>

<!--
Our linear probing search may need to wrap around the end of the array, so there
is another modulo in `findEntry()` to update.
-->
我们的线性探测搜索可能需要从数组末尾回绕，所以 `findEntry()` 里还有另一处取模要更新。

^code next-index (4 before, 1 after)

<!--
This line didn't show up in the profiler since most searches don't wrap.
-->
这行没出现在分析器里，因为多数搜索不会回绕。

<!--
The `findEntry()` function has a sister function, `tableFindString()` that does
a hash table lookup for interning strings. We may as well apply the same
optimizations there too. This function is called only when interning strings,
which wasn't heavily stressed by our benchmark. But a Lox program that created
lots of strings might noticeably benefit from this change.
-->
`findEntry()` 有个姊妹函数 `tableFindString()`，为字符串驻留做哈希表查找。不妨也在那里施加同样的优化。该函数只在驻留字符串时调用，我们的基准并未重压它。但若某段 Lox 程序创建大量字符串，可能会明显受益于这一改动。

^code find-string-index (2 before, 2 after)

<!--
And also when the linear probing wraps around.
-->
线性探测回绕时也一样。

^code find-string-next (3 before, 1 after)

<!--
Let's see if our fixes were worth it. I tweaked that zoological benchmark to
count how many <span name="batch">batches</span> of 10,000 calls it can run in
ten seconds. More batches equals faster performance. On my machine using the
unoptimized code, the benchmark gets through 3,192 batches. After this
optimization, that jumps to 6,249.
-->
看看我们的修复是否值得。我改了那个动物园基准，统计十秒内能跑多少个一万次调用的<span name="batch">批次</span>。批次越多，性能越快。在我机器上，未优化代码跑通 3,192 个批次。优化之后，跳到 6,249。

<img src="image/optimization/hash-chart.png" alt="Bar chart comparing the performance before and after the optimization." />

<!--
That's almost exactly twice as much work in the same amount of time. We made the
VM twice as fast (usual caveat: on this benchmark). That is a massive win when
it comes to optimization. Usually you feel good if you can claw a few percentage
points here or there. Since methods, fields, and global variables are so
prevalent in Lox programs, this tiny optimization improves performance across
the board. Almost every Lox program benefits.
-->
同样时间内几乎正好干了两倍的活。我们让虚拟机快了一倍（照例免责：在此基准上）。这在优化领域是巨大胜利。通常能抠出几个百分点就很开心了。既然方法、字段与全局变量在 Lox 程序里如此普遍，这点微小优化会全面提升性能。几乎每个 Lox 程序都受益。

<aside name="batch">

<!--
Our original benchmark fixed the amount of *work* and then measured the *time*.
Changing the script to count how many batches of calls it can do in ten seconds
fixes the time and measures the work. For performance comparisons, I like the
latter measure because the reported number represents *speed*. You can directly
compare the numbers before and after an optimization. When measuring execution
time, you have to do a little arithmetic to get to a good relative measure of
performance.
-->
原先的基准固定*工作量*再测量*时间*。改成统计十秒内能完成多少批调用，则固定时间、测量工作量。做性能比较时，我更喜欢后者，因为报告的数字代表*速度*。你可以在优化前后直接比较数字。测量执行时间时，得做一点算术才能得到好的相对性能度量。

</aside>

<!--
Now, the point of this section is *not* that the modulo operator is profoundly
evil and you should stamp it out of every program you ever write. Nor is it that
micro-optimization is a vital engineering skill. It's rare that a performance
problem has such a narrow, effective solution. We got lucky.
-->
本节的要点*不是*取模运算符极度邪恶、你该从写过的每个程序里把它铲除。也不是说微优化是关键工程技能。很少有性能问题能有如此狭窄而有效的解药。我们走运了。

<!--
The point is that we didn't *know* that the modulo operator was a performance
drain until our profiler told us so. If we had wandered around our VM's codebase
blindly guessing at hotspots, we likely wouldn't have noticed it. What I want
you to take away from this is how important it is to have a profiler in your
toolbox.
-->
要点是：在分析器告诉我们之前，我们并不*知道*取模是性能漏洞。若我们在虚拟机代码库里盲目猜测热点，多半注意不到。我希望你带走的是：工具箱里有一款性能分析器有多重要。

<!--
To reinforce that point, let's go ahead and run the original benchmark in our
now-optimized VM and see what the profiler shows us. On my machine, `tableGet()`
is still a fairly large chunk of execution time. That's to be expected for a
dynamically typed language. But it has dropped from 72% of the total execution
time down to 35%. That's much more in line with what we'd like to see and shows
that our optimization didn't just make the program faster, but made it faster
*in the way we expected*. Profilers are as useful for verifying solutions as
they are for discovering problems.
-->
为强化这一点，让我们在现已优化的虚拟机上再跑原先的基准，看看分析器怎么说。在我机器上，`tableGet()` 仍占相当大一块执行时间。对动态类型语言来说这在意料之中。但它已从总执行时间的 72% 降到 35%。这更符合我们想看到的，也说明优化不只是让程序更快，而是按我们*预期的方式*更快。性能分析器验证方案与发现问题一样有用。

<!--
-- NaN Boxing
-->
## NaN 装箱

<!--
This next optimization has a very different feel. Thankfully, despite the odd
name, it does not involve punching your grandmother. It's different, but not,
like, *that* different. With our previous optimization, the profiler told us
where the problem was, and we merely had to use some ingenuity to come up with a
solution.
-->
下一项优化手感截然不同。幸好，尽管名字古怪，它并不涉及殴打你的祖母。它不同，但并不是*那种*不同。上一项优化里，分析器告诉我们问题在哪儿，我们只需一点巧思想出方案。

<!--
This optimization is more subtle, and its performance effects more scattered
across the virtual machine. The profiler won't help us come up with this.
Instead, it was invented by <span name="someone">someone</span> thinking deeply
about the lowest levels of machine architecture.
-->
这项优化更微妙，性能影响也更散落在虚拟机各处。分析器帮不了我们想出它。相反，它是由<span name="someone">某人</span>深入思考机器架构最底层而发明的。

<aside name="someone">

<!--
I'm not sure who first came up with this trick. The earliest source I can find
is David Gudeman's 1993 paper "Representing Type Information in Dynamically
Typed Languages". Everyone else cites that. But Gudeman himself says the paper
isn't novel work, but instead "gathers together a body of folklore".
-->
我不确定是谁最先想出这招。我能找到的最早来源是 David Gudeman 1993 年的论文 “Representing Type Information in Dynamically Typed Languages”。别人都引用它。但 Gudeman 自己说，论文并非原创工作，而是“汇集了一堆民间传说”。

<!--
Maybe the inventor has been lost to the mists of time, or maybe it's been
reinvented a number of times. Anyone who ruminates on IEEE 754 long enough
probably starts thinking about trying to stuff something useful into all those
unused NaN bits.
-->
或许发明者已湮没在时间迷雾里，或许它被多次重新发明。凡是对 IEEE 754 沉思够久的人，大概都会开始想：能不能往那些未用的 NaN 位里塞点有用的东西。

</aside>

<!--
Like the heading says, this optimization is called **NaN boxing** or sometimes
**NaN tagging**. Personally I like the latter name because "boxing" tends to imply
some kind of heap-allocated representation, but the former seems to be the more
widely used term. This technique changes how we represent values in the VM.
-->
如标题所言，这项优化叫做 **NaN 装箱**（NaN boxing），有时也叫 **NaN 标记**（NaN tagging）。我个人更喜欢后者，因为“装箱”往往暗示某种堆分配表示，但前者似乎用得更广。这项技术改变我们在虚拟机里表示值的方式。

<!--
On a 64-bit machine, our Value type takes up 16 bytes. The struct has two
fields, a type tag and a union for the payload. The largest fields in the union
are an Obj pointer and a double, which are both 8 bytes. To keep the union field
aligned to an 8-byte boundary, the compiler adds padding after the tag too:
-->
在 64 位机器上，我们的 Value 类型占 16 字节。结构体有两个字段：类型标签，以及载荷的联合。联合里最大的字段是 Obj 指针与 double，都是 8 字节。为让联合字段对齐到 8 字节边界，编译器在标签后也加了填充：

<img src="image/optimization/union.png" alt="Byte layout of the 16-byte tagged union Value." />

<!--
That's pretty big. If we could cut that down, then the VM could pack more values
into the same amount of memory. Most computers have plenty of RAM these days, so
the direct memory savings aren't a huge deal. But a smaller representation means
more Values fit in a cache line. That means fewer cache misses, which affects
*speed*.
-->
这相当大。若能砍小，虚拟机就能在同样多内存里塞进更多值。如今多数计算机有足够 RAM，直接省内存不是大事。但更小的表示意味着更多 Value 能塞进一条缓存行。那意味着更少的缓存未命中，从而影响*速度*。

<!--
If Values need to be aligned to their largest payload size, and a Lox number or
Obj pointer needs a full 8 bytes, how can we get any smaller? In a dynamically
typed language like Lox, each value needs to carry not just its payload, but
enough additional information to determine the value's type at runtime. If a Lox
number is already using the full 8 bytes, where could we squirrel away a couple
of extra bits to tell the runtime "this is a number"?
-->
若 Value 必须按最大载荷尺寸对齐，而 Lox 数字或 Obj 指针需要完整 8 字节，我们怎能再小？在像 Lox 这样的动态类型语言里，每个值不仅要带载荷，还要带足够额外信息以便运行时判定类型。若 Lox 数字已用满 8 字节，我们还能往哪儿藏几位额外比特，告诉运行时“这是个数字”？

<!--
This is one of the perennial problems for dynamic language hackers. It
particularly bugs them because statically typed languages don't generally have
this problem. The type of each value is known at compile time, so no extra
memory is needed at runtime to track it. When your C compiler compiles a 32-bit
int, the resulting variable gets *exactly* 32 bits of storage.
-->
这是动态语言黑客的永恒难题之一。尤其让他们烦的是，静态类型语言通常没有这个问题。每个值的类型在编译期已知，运行时无需额外内存来追踪。当你的 C 编译器编译一个 32 位 int 时，得到的变量正好得到*恰好* 32 位存储。

<!--
Dynamic language folks hate losing ground to the static camp, so they've come up
with a number of very clever ways to pack type information and a payload into a
small number of bits. NaN boxing is one of those. It's a particularly good fit
for languages like JavaScript and Lua, where all numbers are double-precision
floating point. Lox is in that same boat.
-->
动态语言一派讨厌输给静态阵营，于是想出许多极巧妙的办法，把类型信息与载荷塞进少量比特。NaN 装箱就是其中之一。它对 JavaScript、Lua 这类所有数字都是双精度浮点的语言尤其合适。Lox 也在同一条船上。

<!--
-- What is (and is not) a number?
-->
### 什么是（以及不是）数字？

<!--
Before we start optimizing, we need to really understand how our friend the CPU
represents floating-point numbers. Almost all machines today use the same
scheme, encoded in the venerable scroll [IEEE 754][754], known to mortals as the
"IEEE Standard for Floating-Point Arithmetic".
-->
开始优化之前，我们需要真正理解朋友 CPU 如何表示浮点数。如今几乎所有机器都用同一套方案，编码在那卷古老卷轴 [IEEE 754][754] 里，凡人以“IEEE 浮点算术标准”知之。

[754]: https://en.wikipedia.org/wiki/IEEE_754

<!--
In the eyes of your computer, a <span name="hyphen">64-bit</span>,
double-precision, IEEE floating-point number looks like this:
-->
在你的计算机眼里，一个<span name="hyphen">64 位</span>、双精度的 IEEE 浮点数长这样：

<aside name="hyphen">

<!--
That's a lot of hyphens for one sentence.
-->
一句里连字符可真多。

</aside>

<img src="image/optimization/double.png" alt="Bit representation of an IEEE 754 double." />

<!--
*   Starting from the right, the first 52 bits are the **fraction**,
    **mantissa**, or **significand** bits. They represent the significant digits
    of the number, as a binary integer.

*   Next to that are 11 **exponent** bits. These tell you how far the mantissa
    is shifted away from the decimal (well, binary) point.

*   The highest bit is the <span name="sign">**sign bit**</span>, which
    indicates whether the number is positive or negative.
-->
*   从右起，前 52 位是**小数**（fraction）、**尾数**（mantissa）或**有效数**（significand）位。它们以二进制整数表示该数的有效数字。

*   旁边是 11 位**指数**（exponent）。它们告诉你尾数相对十进制（嗯，二进制）小数点偏移多远。

*   最高位是<span name="sign">**符号位**</span>，表明该数是正是负。

<!--
I know that's a little vague, but this chapter isn't a deep dive on
floating point representation. If you want to know how the exponent and mantissa
play together, there are already better explanations out there than I could
write.
-->
我知道这有点含糊，但本章不是浮点表示的深潜。若想知道指数与尾数如何配合，外面已有比我写得更好的解释。

<aside name="sign">

<!--
Since the sign bit is always present, even if the number is zero, that implies
that "positive zero" and "negative zero" have different bit representations, and
indeed, IEEE 754 does distinguish those.
-->
既然符号位始终存在，即便数字是零，也意味着“正零”与“负零”有不同的位表示；的确，IEEE 754 区分它们。

</aside>

<!--
The important part for our purposes is that the spec carves out a special case
exponent. When all of the exponent bits are set, then instead of just
representing a really big number, the value has a different meaning. These
values are "Not a Number" (hence, **NaN**) values. They represent concepts like
infinity or the result of division by zero.
-->
对我们而言，重要的是规范为指数划出了一种特殊情形。当所有指数位都置位时，值不再只是表示一个特别大的数，而是有不同含义。这些值是“非数字”（故称 **NaN**）。它们表示无穷，或除以零的结果之类概念。

<!--
*Any* double whose exponent bits are all set is a NaN, regardless of the
mantissa bits. That means there's lots and lots of *different* NaN bit patterns.
IEEE 754 divides those into two categories. Values where the highest mantissa
bit is 0 are called **signalling NaNs**, and the others are **quiet NaNs**.
Signalling NaNs are intended to be the result of erroneous computations, like
division by zero. A chip <span name="abort">may</span> detect when one of these
values is produced and abort a program completely. They may self-destruct if you
try to read one.
-->
*任何*指数位全置位的 double 都是 NaN，与尾数位无关。这意味着有许许多多*不同的* NaN 位模式。IEEE 754 把它们分成两类。最高尾数位为 0 的叫**信令 NaN**（signalling NaN），其余叫**安静 NaN**（quiet NaN）。信令 NaN 本意是错误计算的结果，比如除以零。芯片<span name="abort">可能</span>在产生这类值时检测到并彻底中止程序。你若试图读一个，它们还可能自爆。

<aside name="abort">

<!--
I don't know if any CPUs actually *do* trap signalling NaNs and abort. The spec
just says they *could*.
-->
我不知道是否有 CPU 真的*会*捕获信令 NaN 并中止。规范只是说它们*可以*。

</aside>

<!--
Quiet NaNs are supposed to be safer to use. They don't represent useful numeric
values, but they should at least not set your hand on fire if you touch them.
-->
安静 NaN 理应更安全。它们不表示有用的数值，但至少不该一碰就让你的手着火。

<!--
Every double with all of its exponent bits set and its highest mantissa bit set
is a quiet NaN. That leaves 52 bits unaccounted for. We'll avoid one of those so
that we don't step on Intel's "QNaN Floating-Point Indefinite" value, leaving us
51 bits. Those remaining bits can be anything. We're talking
2,251,799,813,685,248 unique quiet NaN bit patterns.
-->
每个指数位全置位且最高尾数位也置位的 double 都是安静 NaN。还剩 52 位未交代。我们会避开其中一位，以免踩到 Intel 的 “QNaN Floating-Point Indefinite” 值，于是剩下 51 位。那些剩余位可以是任意内容。我们说的是 2,251,799,813,685,248 种独特的安静 NaN 位模式。

<img src="image/optimization/nan.png" alt="The bits in a double that make it a quiet NaN." />

<!--
This means a 64-bit double has enough room to store all of the various different
numeric floating-point values and *also* has room for another 51 bits of data
that we can use however we want. That's plenty of room to set aside a couple of
bit patterns to represent Lox's `nil`, `true`, and `false` values. But what
about Obj pointers? Don't pointers need a full 64 bits too?
-->
这意味着一个 64 位 double 有足够空间存放各种不同的浮点数值，*还*有另外 51 位数据空间可随意使用。足够留出几种位模式来表示 Lox 的 `nil`、`true` 与 `false`。可 Obj 指针呢？指针不也需要完整 64 位吗？

<!--
Fortunately, we have another trick up our other sleeve. Yes, technically
pointers on a 64-bit architecture are 64 bits. But, no architecture I know of
actually uses that entire address space. Instead, most widely used chips today
only ever use the low <span name="48">48</span> bits. The remaining 16 bits are
either unspecified or always zero.
-->
幸好，另一只袖子里还有一招。是的，技术上 64 位架构上的指针是 64 位。但我所知的架构都没有真用满整个地址空间。相反，当今多数广泛使用的芯片只使用低 <span name="48">48</span> 位。其余 16 位要么未指定，要么始终为零。

<aside name="48">

<!--
48 bits is enough to address 262,144 gigabytes of memory. Modern operating
systems also give each process its own address space, so that should be plenty.
-->
48 位足以寻址 262,144 GB 内存。现代操作系统还给每个进程独立地址空间，应该绰绰有余。

</aside>

<!--
If we've got 51 bits, we can stuff a 48-bit pointer in there with three bits to
spare. Those three bits are just enough to store tiny type tags to distinguish
between `nil`, Booleans, and Obj pointers.
-->
若有 51 位，就能塞进一个 48 位指针，还剩三位。那三位刚好够存微型类型标签，以区分 `nil`、布尔与 Obj 指针。

<!--
That's NaN boxing. Within a single 64-bit double, you can store all of the
different floating-point numeric values, a pointer, or any of a couple of other
special sentinel values. Half the memory usage of our current Value struct,
while retaining all of the fidelity.
-->
这就是 NaN 装箱。在单个 64 位 double 里，你可以存放所有不同的浮点数值、一个指针，或若干其他特殊哨兵值。内存占用是当前 Value 结构体的一半，保真度却全部保留。

<!--
What's particularly nice about this representation is that there is no need to
*convert* a numeric double value into a "boxed" form. Lox numbers *are* just
normal, 64-bit doubles. We still need to *check* their type before we use them,
since Lox is dynamically typed, but we don't need to do any bit shifting or
pointer indirection to go from "value" to "number".
-->
这种表示特别好的一点是：无需把数值 double *转换*成“装箱”形式。Lox 数字*就是*普通的 64 位 double。我们使用前仍需*检查*类型，因为 Lox 是动态类型的，但从“值”到“数字”不必做任何位移或指针间接。

<!--
For the other value types, there is a conversion step, of course. But,
fortunately, our VM hides all of the mechanism to go from values to raw types
behind a handful of macros. Rewrite those to implement NaN boxing, and the rest
of the VM should just work.
-->
对其余值类型，当然有转换步骤。但幸好，虚拟机把从值到原始类型的全部机制藏在少数宏后面。重写那些宏以实现 NaN 装箱，虚拟机其余部分应当就能直接工作。

<!--
-- Conditional support
-->
### 条件支持

<!--
I know the details of this new representation aren't clear in your head yet.
Don't worry, they will crystallize as we work through the implementation. Before
we get to that, we're going to put some compile-time scaffolding in place.
-->
我知道这种新表示的细节在你脑子里还不清晰。别担心，随着我们推进实现，它们会结晶成形。在那之前，先搭一些编译期脚手架。

<!--
For our previous optimization, we rewrote the previous slow code and called it
done. This one is a little different. NaN boxing relies on some very low-level
details of how a chip represents floating-point numbers and pointers. It
*probably* works on most CPUs you're likely to encounter, but you can never be
totally sure.
-->
上一项优化里，我们重写了慢代码就完事。这一项略有不同。NaN 装箱依赖芯片如何表示浮点数与指针的一些非常底层的细节。它*大概*在你可能遇到的多数 CPU 上都能工作，但你永远无法完全确定。

<!--
It would suck if our VM completely lost support for an architecture just because
of its value representation. To avoid that, we'll maintain support for *both*
the old tagged union implementation of Value and the new NaN-boxed form. We
select which representation we want at compile time using this flag:
-->
若虚拟机只因值表示就彻底失去对某架构的支持，那就糟了。为避免如此，我们会同时维持对*两种*表示的支持：旧的带标签联合 Value，以及新的 NaN 装箱形式。编译期用这个标志选择想要的表示：

^code define-nan-boxing (2 before, 1 after)

<!--
If that's defined, the VM uses the new form. Otherwise, it reverts to the old
style. The few pieces of code that care about the details of the value
representation -- mainly the handful of macros for wrapping and unwrapping
Values -- vary based on whether this flag is set. The rest of the VM can
continue along its merry way.
-->
若定义了它，虚拟机用新形式；否则回退到旧风格。少数关心值表示细节的代码——主要是包装与解包 Value 的那几个宏——会随该标志是否设置而变化。虚拟机其余部分可以继续自得其乐。

<!--
Most of the work happens in the "value" module where we add a section for the
new type.
-->
大部分工作发生在 “value” 模块，我们为新类型加一节。

^code nan-boxing (2 before, 1 after)

<!--
When NaN boxing is enabled, the actual type of a Value is a flat, unsigned
64-bit integer. We could use double instead, which would make the macros for
dealing with Lox numbers a little simpler. But all of the other macros need to
do bitwise operations and uint64_t is a much friendlier type for that. Outside
of this module, the rest of the VM doesn't really care one way or the other.
-->
启用 NaN 装箱时，Value 的实际类型是一个扁平的无符号 64 位整数。我们本可用 double，那样处理 Lox 数字的宏会简单一点。但其余所有宏都需要做按位运算，uint64_t 对此友好得多。在此模块之外，虚拟机其余部分其实并不在乎用哪种。

<!--
Before we start re-implementing those macros, we close the `#else` branch of the
`#ifdef` at the end of the definitions for the old representation.
-->
开始重实现那些宏之前，我们在旧表示定义的末尾关闭 `#ifdef` 的 `#else` 分支。

^code end-if-nan-boxing (1 before, 2 after)

<!--
Our remaining task is simply to fill in that first `#ifdef` section with new
implementations of all the stuff already in the `#else` side. We'll work through
it one value type at a time, from easiest to hardest.
-->
剩下的任务只是用新实现对那个 `#ifdef` 第一节填满 `#else` 侧已有的全部东西。我们会按值类型逐个推进，从最易到最难。

<!--
-- Numbers
-->
### 数字

<!--
We'll start with numbers since they have the most direct representation under
NaN boxing. To "convert" a C double to a NaN-boxed clox Value, we don't need to
touch a single bit -- the representation is exactly the same. But we do need to
convince our C compiler of that fact, which we made harder by defining Value to
be uint64_t.
-->
我们从数字开始，因为在 NaN 装箱下它们的表示最直接。把 C 的 double “转换”成 NaN 装箱的 clox Value，我们不必动任何一个比特——表示完全一样。但我们得说服 C 编译器接受这一事实；而把 Value 定义成 uint64_t，让这件事更难了。

<!--
We need to get the compiler to take a set of bits that it thinks are a double
and use those same bits as a uint64_t, or vice versa. This is called **type
punning**. C and C++ programmers have been doing this since the days of bell
bottoms and 8-tracks, but the language specifications have <span
name="hesitate">hesitated</span> to say which of the many ways to do this is
officially sanctioned.
-->
我们需要让编译器把一组它以为是 double 的比特，当作 uint64_t 来用，或反过来。这叫做**类型双关**（type punning）。C 与 C++ 程序员从喇叭裤与八轨磁带的年代就在这么干，但语言规范一直<span
name="hesitate">犹豫</span>不肯说众多做法里哪一种获官方认可。

<aside name="hesitate" class="bottom">

<!--
Spec authors don't like type punning because it makes optimization harder. A key
optimization technique is reordering instructions to fill the CPU's execution
pipelines. A compiler can reorder code only when doing so doesn't have a
user-visible effect, obviously.
-->
规范作者不喜欢类型双关，因为它让优化更难。一项关键优化技术是重排指令以填满 CPU 执行流水线。显然，编译器只有在重排没有用户可见效果时才能这么做。

<!--
Pointers make that harder. If two pointers point to the same value, then a write
through one and a read through the other cannot be reordered. But what about two
pointers of *different* types? If those could point to the same object, then
basically *any* two pointers could be aliases to the same value. That
drastically limits the amount of code the compiler is free to rearrange.
-->
指针让事情更难。若两个指针指向同一值，则通过一个写入、通过另一个读取不能重排。可若是*不同*类型的两个指针呢？若它们可以指向同一对象，那么基本上*任意*两个指针都可能是同一值的别名。这大幅限制了编译器可自由重排的代码量。

<!--
To avoid that, compilers want to assume **strict aliasing** -- pointers of
incompatible types cannot point to the same value. Type punning, by nature,
breaks that assumption.
-->
为避免如此，编译器想假定**严格别名**（strict aliasing）——不兼容类型的指针不能指向同一值。类型双关本质上打破了该假定。

</aside>

<!--
I know one way to convert a `double` to `Value` and back that I believe is
supported by both the C and C++ specs. Unfortunately, it doesn't fit in a single
expression, so the conversion macros have to call out to helper functions.
Here's the first macro:
-->
我知道一种把 `double` 转成 `Value` 再转回来的办法，我相信 C 与 C++ 规范都支持。不幸的是，它放不进单个表达式，所以转换宏得调用辅助函数。第一个宏如下：

^code number-val (1 before, 2 after)

<!--
That macro passes the double here:
-->
该宏把 double 传到这里：

^code num-to-value (1 before, 2 after)

<!--
I know, weird, right? The way to treat a series of bytes as having a different
type without changing their value at all is `memcpy()`? This looks horrendously
slow: Create a local variable. Pass its address to the operating system through
a syscall to copy a few bytes. Then return the result, which is the exact same
bytes as the input. Thankfully, because this *is* the supported idiom for type
punning, most compilers recognize the pattern and optimize away the `memcpy()`
entirely.
-->
我知道，怪对吧？把一串字节当成不同类型、却完全不改变其值的办法，居然是 `memcpy()`？这看起来慢得可怕：创建局部变量；通过系统调用把地址交给操作系统去复制几个字节；再返回结果——而结果与输入字节完全相同。幸好，因为这*就是*类型双关的受支持惯用法，多数编译器能认出这一模式并彻底优化掉 `memcpy()`。

<!--
"Unwrapping" a Lox number is the mirror image.
-->
“解包”一个 Lox 数字是镜像操作。

^code as-number (1 before, 2 after)

<!--
That macro calls this function:
-->
该宏调用这个函数：

^code value-to-num (1 before, 2 after)

<!--
It works exactly the same except we swap the types. Again, the compiler will
eliminate all of it. Even though those calls to
`memcpy()` will disappear, we still need to show the compiler *which* `memcpy()`
we're calling so we also need an <span name="union">include</span>.
-->
它完全一样，只是交换了类型。同样，编译器会全部消掉。即便那些 `memcpy()` 调用会消失，我们仍需让编译器知道我们调用的是*哪一个* `memcpy()`，所以还需要一个<span name="union">头文件包含</span>。

<aside name="union" class="bottom">

<!--
If you find yourself with a compiler that does not optimize the `memcpy()` away,
try this instead:
-->
若你碰到不会优化掉 `memcpy()` 的编译器，试试这个：

```c
double valueToNum(Value value) {
  union {
    uint64_t bits;
    double num;
  } data;
  data.bits = value;
  return data.num;
}
```

</aside>

^code include-string (1 before, 2 after)

<!--
That was a lot of code to ultimately do nothing but silence the C type checker.
Doing a runtime type *test* on a Lox number is a little more interesting. If all
we have are exactly the bits for a double, how do we tell that it *is* a double?
It's time to get bit twiddling.
-->
为了最终只是让 C 类型检查器闭嘴，这可写了不少代码。对 Lox 数字做运行时类型*测试*更有趣一点。若我们手里恰好是 double 的那些比特，怎么判断它*是* double？是时候玩位操作了。

^code is-number (1 before, 2 after)

<!--
We know that every Value that is *not* a number will use a special quiet NaN
representation. And we presume we have correctly avoided any of the meaningful
NaN representations that may actually be produced by doing arithmetic on
numbers.
-->
我们知道每个*不是*数字的 Value 都会使用特殊的安静 NaN 表示。我们也假定自己正确避开了那些对数字做算术时可能真正产生的有意义的 NaN 表示。

<!--
If the double has all of its NaN bits set, and the quiet NaN bit set, and one
more for good measure, we can be <span name="certain">pretty certain</span> it
is one of the bit patterns we ourselves have set aside for other types. To check
that, we mask out all of the bits except for our set of quiet NaN bits. If *all*
of those bits are set, it must be a NaN-boxed value of some other Lox type.
Otherwise, it is actually a number.
-->
若 double 的全部 NaN 位都置位、安静 NaN 位也置位，再多一位以防万一，我们就能<span name="certain">相当确信</span>它是我们为自己其他类型预留的位模式之一。要检查这一点，我们掩掉安静 NaN 位集合以外的所有位。若*所有*那些位都置位，它必定是某种其他 Lox 类型的 NaN 装箱值。否则，它其实是个数字。

<aside name="certain">

<!--
Pretty certain, but not strictly guaranteed. As far as I know, there is nothing
preventing a CPU from producing a NaN value as the result of some operation
whose bit representation collides with ones we have claimed. But in my tests
across a number of architectures, I haven't seen it happen.
-->
相当确信，但并非严格保证。据我所知，没有什么能阻止 CPU 在某次运算中产生一个位表示与我们声称的模式相撞的 NaN。但在我跨若干架构的测试里，尚未见过。

</aside>

<!--
The set of quiet NaN bits are declared like this:
-->
安静 NaN 位集合声明如下：

^code qnan (1 before, 2 after)

<!--
It would be nice if C supported binary literals. But if you do the conversion,
you'll see that value is the same as this:
-->
若 C 支持二进制字面量就好了。但若你做转换，会看到该值与这个相同：

<img src="image/optimization/qnan.png" alt="The quiet NaN bits." />

<!--
This is exactly all of the exponent bits, plus the quiet NaN bit, plus one extra
to dodge that Intel value.
-->
这恰好是全部指数位，加上安静 NaN 位，再加上一位额外的，好躲开那个 Intel 值。

<!--
-- Nil, true, and false
-->
### nil、true 与 false

<!--
The next type to handle is `nil`. That's pretty simple since there's only one
`nil` value and thus we need only a single bit pattern to represent it. There
are two other singleton values, the two Booleans, `true` and `false`. This calls
for three total unique bit patterns.
-->
下一个要处理的类型是 `nil`。这很简单，因为只有一个 `nil` 值，因而只需一种位模式来表示它。还有两个单例值：两个布尔 `true` 与 `false`。一共需要三种独特位模式。

<!--
Two bits give us four different combinations, which is plenty. We claim the two
lowest bits of our unused mantissa space as a "type tag" to determine which of
these three singleton values we're looking at. The three type tags are defined
like so:
-->
两位给出四种不同组合，足够了。我们把未用尾数空间的最低两位声明为“类型标签”，以判定看到的是这三个单例中的哪一个。三个类型标签定义如下：

^code tags (1 before, 2 after)

<!--
Our representation of `nil` is thus all of the bits required to define our
quiet NaN representation along with the `nil` type tag bits:
-->
因此，我们对 `nil` 的表示是定义安静 NaN 表示所需的全部位，再加上 `nil` 类型标签位：

<img src="image/optimization/nil.png" alt="The bit representation of the nil value." />

<!--
In code, we check the bits like so:
-->
在代码里，我们这样检查这些位：

^code nil-val (2 before, 1 after)

<!--
We simply bitwise <span class="small-caps">OR</span> the quiet NaN bits and the
type tag, and then do a little cast dance to teach the C compiler what we want
those bits to mean.
-->
我们只需对安静 NaN 位与类型标签做按位 <span class="small-caps">OR</span>，再跳一小段强制转换的舞，好教 C 编译器这些位想表示什么。

<!--
Since `nil` has only a single bit representation, we can use <span
name="equal">equality</span> on uint64_t to see if a Value is `nil`.
-->
既然 `nil` 只有一种位表示，我们可以对 uint64_t 用<span
name="equal">相等</span>比较来看一个 Value 是否为 `nil`。

^code is-nil (2 before, 1 after)

<!--
You can guess how we define the `true` and `false` values.
-->
你可以猜到我们如何定义 `true` 与 `false` 值。

^code false-true-vals (2 before, 1 after)

<!--
The bits look like this:
-->
那些位长这样：

<img src="image/optimization/bools.png" alt="The bit representation of the true and false values." />

<!--
To convert a C bool into a Lox Boolean, we rely on these two singleton values
and the good old conditional operator.
-->
把 C 的 bool 转成 Lox 布尔，我们依赖这两个单例值，以及好用的条件运算符。

^code bool-val (2 before, 1 after)

<!--
There's probably a cleverer bitwise way to do this, but my hunch is that the
compiler can figure one out faster than I can. Going the other direction is
simpler.
-->
大概有更巧妙的按位做法，但我直觉是编译器能比我更快想出来。反过来方向更简单。

^code as-bool (2 before, 1 after)

<!--
Since we know there are exactly two Boolean bit representations in Lox -- unlike
in C where any non-zero value can be considered "true" -- if it ain't `true`, it
must be `false`. This macro does assume you call it only on a Value that you
know *is* a Lox Boolean. To check that, there's one more macro.
-->
既然我们知道 Lox 里恰好有两种布尔位表示——不像 C 里任何非零值都可视为“真”——若它不是 `true`，就必定是 `false`。该宏假定你只对已知*是* Lox 布尔的 Value 调用它。要检查这一点，还有一个宏。

^code is-bool (2 before, 1 after)

<!--
That looks a little strange. A more obvious macro would look like this:
-->
这看起来有点怪。更显而易见的宏会像这样：

```c
#define IS_BOOL(v) ((v) == TRUE_VAL || (v) == FALSE_VAL)
```

<!--
Unfortunately, that's not safe. The expansion mentions `v` twice, which means if
that expression has any side effects, they will be executed twice. We could have
the macro call out to a separate function, but, ugh, what a chore.
-->
不幸的是，这不安全。展开提到 `v` 两次，意味着若该表达式有任何副作用，它们会被执行两次。我们可以让宏去调一个单独函数，可，呃，多麻烦。

<!--
Instead, we bitwise <span class="small-caps">OR</span> a 1 onto the value to
merge the only two valid Boolean bit patterns. That leaves three potential
states the value can be in:
-->
取而代之，我们对值按位 <span class="small-caps">OR</span> 上 1，合并仅有的两种合法布尔位模式。于是值可能处于三种状态：

<!--
1. It was `FALSE_VAL` and has now been converted to `TRUE_VAL`.

2. It was `TRUE_VAL` and the `| 1` did nothing and it's still `TRUE_VAL`.

3. It's some other, non-Boolean value.
-->
1. 它曾是 `FALSE_VAL`，现已变成 `TRUE_VAL`。

2. 它曾是 `TRUE_VAL`，`| 1` 什么也没做，仍是 `TRUE_VAL`。

3. 它是某个其他的、非布尔值。

<!--
At that point, we can simply compare the result to `TRUE_VAL` to see if we're
in the first two states or the third.
-->
此时，我们只需把结果与 `TRUE_VAL` 比较，看我们处于前两种状态还是第三种。

<!--
-- Objects
-->
### 对象

<!--
The last value type is the hardest. Unlike the singleton values, there are
billions of different pointer values we need to box inside a NaN. This means we
need both some kind of tag to indicate that these particular NaNs *are* Obj
pointers, and room for the addresses themselves.
-->
最后一个值类型最难。与单例值不同，我们需要把数十亿种不同的指针值装箱进 NaN。这意味着我们既需要某种标签标明这些特别的 NaN *是* Obj 指针，也需要给地址本身留空间。

<!--
The tag bits we used for the singleton values are in the region where I decided
to store the pointer itself, so we can't easily use a different <span
name="ptr">bit</span> there to indicate that the value is an object reference.
However, there is another bit we aren't using. Since all our NaN values are not
numbers -- it's right there in the name -- the sign bit isn't used for anything.
We'll go ahead and use that as the type tag for objects. If one of our quiet
NaNs has its sign bit set, then it's an Obj pointer. Otherwise, it must be one
of the previous singleton values.
-->
单例值用的标签位，落在我决定存放指针本身的区域，所以我们没法轻易在那里用另一个<span
name="ptr">比特</span>标明该值是对象引用。不过，还有一位我们没用。既然我们所有的 NaN 值都不是数字——名字里就写着——符号位派不上用场。我们就用它当对象的类型标签。若某个安静 NaN 的符号位置位，那它就是 Obj 指针；否则，必定是先前那些单例之一。

<aside name="ptr">

<!--
We actually *could* use the lowest bits to store the type tag even when the
value is an Obj pointer. That's because Obj pointers are always aligned to an
8-byte boundary since Obj contains a 64-bit field. That, in turn, implies that
the three lowest bits of an Obj pointer will always be zero. We could store
whatever we wanted in there and just mask it off before dereferencing the
pointer.
-->
其实我们*可以*在值是 Obj 指针时，仍用最低几位存类型标签。因为 Obj 含有 64 位字段，Obj 指针始终对齐到 8 字节边界。这进而意味着 Obj 指针的最低三位始终为零。我们可以在那里存任意内容，解引用前再掩掉即可。

<!--
This is another value representation optimization called **pointer tagging**.
-->
这是另一种值表示优化，叫做**指针标记**（pointer tagging）。

</aside>

<!--
If the sign bit is set, then the remaining low bits store the pointer to the
Obj:
-->
若符号位置位，则其余低位存放指向 Obj 的指针：

<img src="image/optimization/obj.png" alt="Bit representation of an Obj* stored in a Value." />

<!--
To convert a raw Obj pointer to a Value, we take the pointer and set all of the
quiet NaN bits and the sign bit.
-->
把原始 Obj 指针转成 Value，我们取该指针，置上全部安静 NaN 位与符号位。

^code obj-val (1 before, 2 after)

<!--
The pointer itself is a full 64 bits, and in <span name="safe">principle</span>,
it could thus overlap with some of those quiet NaN and sign bits. But in
practice, at least on the architectures I've tested, everything above the 48th
bit in a pointer is always zero. There's a lot of casting going on here, which
I've found is necessary to satisfy some of the pickiest C compilers, but the
end result is just jamming some bits together.
-->
指针本身是完整 64 位，<span name="safe">原则上</span>可能与那些安静 NaN 位和符号位重叠。但实践中，至少在我测试过的架构上，指针第 48 位以上始终为零。这里有大量强制转换，我发现这对满足某些最挑剔的 C 编译器是必要的，但最终结果只是把一些比特塞到一起。

<aside name="safe">

<!--
I try to follow the letter of the law when it comes to the code in this book, so
this paragraph is dubious. There comes a point when optimizing where you push
the boundary of not just what the *spec says* you can do, but what a real
compiler and chip let you get away with.
-->
谈到本书里的代码，我尽量字面遵守法律，所以这一段有点可疑。优化到某个地步，你推的不只是*规范说*你能做什么的边界，还有真实编译器与芯片让你侥幸过关的边界。

<!--
There are risks when stepping outside of the spec, but there are rewards in that
lawless territory too. It's up to you to decide if the gains are worth it.
-->
踏出规范有风险，但那片无法之地也有回报。收益是否值得，由你决定。

</aside>

<!--
We define the sign bit like so:
-->
我们这样定义符号位：

^code sign-bit (2 before, 2 after)

<!--
To get the Obj pointer back out, we simply mask off all of those extra bits.
-->
要取出 Obj 指针，只需掩掉所有那些额外位。

^code as-obj (1 before, 2 after)

<!--
The tilde (`~`), if you haven't done enough bit manipulation to encounter it
before, is bitwise <span class="small-caps">NOT</span>. It toggles all ones and
zeroes in its operand. By masking the value with the bitwise negation of the
quiet NaN and sign bits, we *clear* those bits and let the pointer bits remain.
-->
波浪号（`~`），若你还没做过足够多位操作而没遇见过，就是按位 <span class="small-caps">NOT</span>。它翻转操作数中所有的一与零。用安静 NaN 与符号位的按位取反去掩值，我们*清掉*那些位，让指针位留下。

<!--
One last macro:
-->
最后一个宏：

^code is-obj (1 before, 2 after)

<!--
A Value storing an Obj pointer has its sign bit set, but so does any negative
number. To tell if a Value is an Obj pointer, we need to check that both the
sign bit and all of the quiet NaN bits are set. This is similar to how we detect
the type of the singleton values, except this time we use the sign bit as the
tag.
-->
存放 Obj 指针的 Value 符号位置位，但任何负数也是。要判断一个 Value 是否为 Obj 指针，需要检查符号位与全部安静 NaN 位都置位。这与检测单例值类型的方式相似，只是这次用符号位当标签。

<!--
-- Value functions
-->
### 值相关函数

<!--
The rest of the VM usually goes through the macros when working with Values, so
we are almost done. However, there are a couple of functions in the "value"
module that peek inside the otherwise black box of Value and work with its
encoding directly. We need to fix those too.
-->
虚拟机其余部分处理 Value 时通常走那些宏，所以我们几乎完成了。不过，“value” 模块里还有几个函数会窥视 Value 这个黑盒并直接处理其编码。那些也需要修。

<!--
The first is `printValue()`. It has separate code for each value type. We no
longer have an explicit type enum we can switch on, so instead we use a series
of type tests to handle each kind of value.
-->
第一个是 `printValue()`。它对每种值类型有单独代码。我们不再有可 switch 的显式类型枚举，于是改用一系列类型测试处理每类值。

^code print-value (1 before, 1 after)

<!--
This is technically a tiny bit slower than a switch, but compared to the
overhead of actually writing to a stream, it's negligible.
-->
技术上这比 switch 慢一点点，但与真正写入流的开销相比，可忽略不计。

<!--
We still support the original tagged union representation, so we keep the old
code and enclose it in the `#else` conditional section.
-->
我们仍支持原先的带标签联合表示，所以保留旧代码，并包在 `#else` 条件节里。

^code end-print-value (1 before, 1 after)

<!--
The other operation is testing two values for equality.
-->
另一项操作是测试两个值是否相等。

^code values-equal (1 before, 1 after)

<!--
It doesn't get much simpler than that! If the two bit representations are
identical, the values are equal. That does the right thing for the singleton
values since each has a unique bit representation and they are only equal to
themselves. It also does the right thing for Obj pointers, since objects use
identity for equality -- two Obj references are equal only if they point to the
exact same object.
-->
不能更简单了！若两位表示相同，值就相等。这对单例值做对了，因为每个都有独特位表示且只等于自己。对 Obj 指针也对了，因为对象用同一性判等——两个 Obj 引用只有指向完全同一对象时才相等。

<!--
It's *mostly* correct for numbers too. Most floating-point numbers with
different bit representations are distinct numeric values. Alas, IEEE 754
contains a pothole to trip us up. For reasons that aren't entirely clear to me,
the spec mandates that NaN values are *not* equal to *themselves*. This isn't a
problem for the special quiet NaNs that we are using for our own purposes. But
it's possible to produce a "real" arithmetic NaN in Lox, and if we want to
correctly implement IEEE 754 numbers, then the resulting value is not supposed
to be equal to itself. More concretely:
-->
对数字也*大体*正确。多数位表示不同的浮点数是不同的数值。可惜 IEEE 754 有个坑等着绊我们。出于我不完全清楚的原因，规范规定 NaN 值*不*等于*自身*。这对我们自用的特殊安静 NaN 不是问题。但有可能在 Lox 里产生“真正的”算术 NaN；若我们想正确实现 IEEE 754 数字，则结果值不该等于自身。更具体地说：

```lox
var nan = 0/0;
print nan == nan;
```

<!--
IEEE 754 says this program is supposed to print "false". It does the right thing
with our old tagged union representation because the `VAL_NUMBER` case applies
`==` to two values that the C compiler knows are doubles. Thus the compiler
generates the right CPU instruction to perform an IEEE floating-point equality.
-->
IEEE 754 说该程序应打印 “false”。用旧的带标签联合表示时它做对了，因为 `VAL_NUMBER` 分支对 C 编译器已知为 double 的两个值应用 `==`。于是编译器生成正确的 CPU 指令来做 IEEE 浮点相等比较。

<!--
Our new representation breaks that by defining Value to be a uint64_t. If we
want to be *fully* compliant with IEEE 754, we need to handle this case.
-->
新表示把 Value 定义成 uint64_t，打破了这一点。若想*完全*符合 IEEE 754，需要处理这一情形。

^code nan-equality (1 before, 1 after)

<!--
I know, it's weird. And there is a performance cost to doing this type test
every time we check two Lox values for equality. If we are willing to sacrifice
a little <span name="java">compatibility</span> -- who *really* cares if NaN is
not equal to itself? -- we could leave this off. I'll leave it up to you to
decide how pedantic you want to be.
-->
我知道，这很怪。而且每次检查两个 Lox 值是否相等都做这个类型测试有性能代价。若我们愿意牺牲一点<span name="java">兼容性</span>——谁*真的*在乎 NaN 是否不等于自身？——可以省掉。多迂腐由你决定。

<aside name="java">

<!--
In fact, jlox gets NaN equality wrong. Java does the right thing when you
compare primitive doubles using `==`, but not if you box those to Double or
Object and compare them using `equals()`, which is how jlox implements equality.
-->
事实上，jlox 的 NaN 相等性是错的。用 `==` 比较原始 double 时 Java 做对了，但若装箱成 Double 或 Object 再用 `equals()` 比较——而这正是 jlox 实现相等的方式——就不对了。

</aside>

<!--
Finally, we close the conditional compilation section around the old
implementation.
-->
最后，我们关闭旧实现周围的条件编译节。

^code end-values-equal (1 before, 1 after)

<!--
And that's it. This optimization is complete, as is our clox virtual machine.
That was the last line of new code in the book.
-->
就是这样。这项优化完成了，我们的 clox 虚拟机也完成了。那是本书最后一行新代码。

<!--
-- Evaluating performance
-->
### 评估性能

<!--
The code is done, but we still need to figure out if we actually made anything
better with these changes. Evaluating an optimization like this is very
different from the previous one. There, we had a clear hotspot visible in the
profiler. We fixed that part of the code and could instantly see the hotspot
get faster.
-->
代码写完了，但我们仍需弄清这些改动是否真让事情更好了。评估这类优化与上一项很不一样。那里，分析器里有清晰可见的热点。我们修了那部分代码，立刻就能看到热点变快。

<!--
The effects of changing the value representation are more diffused. The macros
are expanded in place wherever they are used, so the performance changes are
spread across the codebase in a way that's hard for many profilers to track
well, especially in an <span name="opt">optimized</span> build.
-->
改变值表示的效果更弥散。宏在使用处就地展开，所以性能变化散落在代码库各处，许多分析器难以很好追踪——尤其是在<span name="opt">优化</span>构建里。

<aside name="opt">

<!--
When doing profiling work, you almost always want to profile an optimized
"release" build of your program since that reflects the performance story your
end users experience. Compiler optimizations, like inlining, can dramatically
affect which parts of the code are performance hotspots. Hand-optimizing a debug
build risks sending you off "fixing" problems that the optimizing compiler will
already solve for you.
-->
做性能分析时，你几乎总想分析程序的优化“发布”构建，因为那反映最终用户体验到的性能故事。编译器优化（如内联）会剧烈影响哪些代码部分是性能热点。手工优化调试构建，有把你送去“修复”优化编译器本已替你解决的问题的风险。

<!--
Make sure you don't accidentally benchmark and optimize your debug build. I seem
to make that mistake at least once a year.
-->
确保别一不小心对调试构建做基准测试与优化。我似乎每年至少犯一次这错。

</aside>

<!--
We also can't easily *reason* about the effects of our change. We've made values
smaller, which reduces cache misses all across the VM. But the actual real-world
performance effect of that change is highly dependent on the memory use of the
Lox program being run. A tiny Lox microbenchmark may not have enough values
scattered around in memory for the effect to be noticeable, and even things like
the addresses handed out to us by the C memory allocator can impact the results.
-->
我们也无法轻易*推理*改动的效果。我们让值变小了，从而减少虚拟机各处的缓存未命中。但该改动的真实世界性能效果高度依赖所跑 Lox 程序的内存使用。小小的 Lox 微基准可能没有足够多散落在内存里的值让效果可察觉，甚至 C 内存分配器交给我们的地址之类也会影响结果。

<!--
If we did our job right, basically everything gets a little faster, especially
on larger, more complex Lox programs. But it is possible that the extra bitwise
operations we do when NaN-boxing values nullify the gains from the better
memory use. Doing performance work like this is unnerving because you can't
easily *prove* that you've made the VM better. You can't point to a single
surgically targeted microbenchmark and say, "There, see?"
-->
若我们干得好，基本上一切都会快一点，尤其在更大、更复杂的 Lox 程序上。但也可能 NaN 装箱时多做的按位运算抵消了更好内存使用带来的收益。做这类性能工作令人不安，因为你无法轻易*证明*虚拟机变好了。你没法指着单个手术刀式微基准说：“瞧，看见了吧？”

<!--
Instead, what we really need is a *suite* of larger benchmarks. Ideally, they
would be distilled from real-world applications -- not that such a thing exists
for a toy language like Lox. Then we can measure the aggregate performance
changes across all of those. I did my best to cobble together a handful of
larger Lox programs. On my machine, the new value representation seems to make
everything roughly 10% faster across the board.
-->
相反，我们真正需要的是一套*更大*的基准。理想情况下，它们从真实世界应用蒸馏而来——对 Lox 这种玩具语言来说，那种东西并不存在。然后我们可以跨全部基准测量总体性能变化。我尽力拼凑了几份较大的 Lox 程序。在我机器上，新值表示似乎全面大约快了 10%。

<!--
That's not a huge improvement, especially compared to the profound effect of
making hash table lookups faster. I added this optimization in large part
because it's a good example of a certain *kind* of performance work you may
experience, and honestly, because I think it's technically really cool. It might
not be the first thing I would reach for if I were seriously trying to make clox
faster. There is probably other, lower-hanging fruit.
-->
这不算巨大改进，尤其相比让哈希表查找变快的深刻效果。我加入这项优化，很大程度上是因为它是你可能经历的某*类*性能工作的好例子，老实说，也因为我觉得技术上真酷。若我认真想让 clox 更快，这大概不是我会首先伸手去够的。大概还有其他更低垂的果实。

<!--
But, if you find yourself working on a program where all of the easy wins have
been taken, then at some point you may want to think about tuning your value
representation. I hope this chapter has shined a light on some of the options
you have in that area.
-->
但若你发现自己在做一个轻松胜利都已被拿走的程序，总有一天你可能想调调值表示。希望本章照亮了那一领域你拥有的一些选项。

<!--
-- Where to Next
-->
## 下一步去哪里

<!--
We'll stop here with the Lox language and our two interpreters. We could tinker
on it forever, adding new language features and clever speed improvements. But,
for this book, I think we've reached a natural place to call our work complete.
I won't rehash everything we've learned in the past many pages. You were there
with me and you remember. Instead, I'd like to take a minute to talk about where
you might go from here. What is the next step in your programming language
journey?
-->
我们在此停下 Lox 语言与两台解释器。我们可以永远摆弄它，加新语言特性与巧妙提速。但对本书而言，我认为已到了可以宣告工作完成的自然之处。我不会复述过去许多页学到的一切。你与我同在，你记得。相反，我想花一分钟谈谈你可能从这里去哪儿。你的程序设计语言之旅，下一步是什么？

<!--
Most of you probably won't spend a significant part of your career working in
compilers or interpreters. It's a pretty small slice of the computer science
academia pie, and an even smaller segment of software engineering in industry.
That's OK. Even if you never work on a compiler again in your life, you will
certainly *use* one, and I hope this book has equipped you with a better
understanding of how the programming languages you use are designed and
implemented.
-->
你们多数人大概不会把职业生涯的重要部分花在编译器或解释器上。那是计算机科学学术派里相当小的一块，在工业软件工程里更小。没关系。即便你这辈子再也不做编译器，你也肯定会*使用*一台；希望本书让你更好理解所用程序设计语言如何设计与实现。

<!--
You have also learned a handful of important, fundamental data structures and
gotten some practice doing low-level profiling and optimization work. That kind
of expertise is helpful no matter what domain you program in.
-->
你也学到了若干重要的基础数据结构，并练过底层性能分析与优化。无论你在哪个领域编程，那种专长都有帮助。

<!--
I also hope I gave you a new way of <span name="domain">looking</span> at and
solving problems. Even if you never work on a language again, you may be
surprised to discover how many programming problems can be seen as
language-*like*. Maybe that report generator you need to write can be modeled as
a series of stack-based "instructions" that the generator "executes". That user
interface you need to render looks an awful lot like traversing an AST.
-->
我也希望给你一种新的<span name="domain">看待</span>与解决问题的方式。即便你再也不做语言，你可能会惊讶地发现：有多少编程问题可以看成语言*般*的。或许你要写的报表生成器，可以建模成生成器“执行”的一系列基于栈的“指令”。你要渲染的用户界面，看着极像遍历一棵 AST。

<aside name="domain">

<!--
This goes for other domains too. I don't think there's a single topic I've
learned in programming -- or even outside of programming -- that I haven't ended
up finding useful in other areas. One of my favorite aspects of software
engineering is how much it rewards those with eclectic interests.
-->
这对其他领域也成立。我不认为我在编程里——甚至编程外——学过的任何一个主题，最终没有在其他领域派上用场。软件工程我最喜欢的一面之一，就是它多么奖励兴趣庞杂的人。

</aside>

<!--
If you do want to go further down the programming language rabbit hole, here
are some suggestions for which branches in the tunnel to explore:
-->
若你确实想沿程序设计语言的兔子洞再往下走，以下是一些建议，可探索隧道里哪些岔路：

<!--
*   Our simple, single-pass bytecode compiler pushed us towards mostly runtime
    optimization. In a mature language implementation, compile-time optimization
    is generally more important, and the field of compiler optimizations is
    incredibly rich. Grab a classic <span name="cooper">compilers</span> book,
    and rebuild the front end of clox or jlox to be a sophisticated compilation
    pipeline with some interesting intermediate representations and optimization
    passes.

    Dynamic typing will place some restrictions on how far you can go, but there
    is still a lot you can do. Or maybe you want to take a big leap and add
    static types and a type checker to Lox. That will certainly give your front
    end a lot more to chew on.
-->
*   我们简单的单遍字节码编译器把我们推向了主要做运行时优化。在成熟的语言实现里，编译期优化通常更重要，而编译器优化领域极其丰富。拿一本经典<span name="cooper">编译器</span>书，把 clox 或 jlox 的前端重建成带有有趣中间表示与优化遍的精致编译流水线。

    动态类型会限制你能走多远，但仍有许多可做。或许你想迈一大步，给 Lox 加上静态类型与类型检查器。那肯定会让前端有更多可啃的。

    <aside name="cooper">

    <!--
    I like Cooper and Torczon's *Engineering a Compiler* for this. Appel's
    *Modern Compiler Implementation* books are also well regarded.
    -->
    这方面我喜欢 Cooper 与 Torczon 的 *Engineering a Compiler*。Appel 的 *Modern Compiler Implementation* 系列也广受好评。

    </aside>

<!--
*   In this book, I aim to be correct, but not particularly rigorous. My goal is
    mostly to give you an *intuition* and a feel for doing language work. If you
    like more precision, then the whole world of programming language academia
    is waiting for you. Languages and compilers have been studied formally since
    before we even had computers, so there is no shortage of books and papers on
    parser theory, type systems, semantics, and formal logic. Going down this
    path will also teach you how to read CS papers, which is a valuable skill in
    its own right.
-->
*   在本书中，我力求正确，但不特别严谨。我的目标主要是给你做语言工作的*直觉*与手感。若你喜欢更多精确性，整个程序设计语言学术界在等你。语言与编译器在我们有计算机之前就已被形式化研究，所以解析器理论、类型系统、语义与形式逻辑的书与论文并不短缺。走这条路也会教你如何读 CS 论文——这本身就是一项宝贵技能。

<!--
*   Or, if you just really enjoy hacking on and making languages, you can take
    Lox and turn it into your own <span name="license">plaything</span>. Change
    the syntax to something that delights your eye. Add missing features or
    remove ones you don't like. Jam new optimizations in there.
-->
*   或者，若你只是真的喜欢捣鼓与制造语言，可以把 Lox 变成你自己的<span name="license">玩物</span>。把语法改成赏心悦目的样子。加上缺失的特性，或去掉你不喜欢的。塞进新优化。

    <aside name="license">

    <!--
    The *text* of this book is copyrighted to me, but the *code* and the
    implementations of jlox and clox use the very permissive [MIT license][].
    You are more than welcome to [take either of those interpreters][source] and
    do whatever you want with them. Go to town.
    -->
    本书的*正文*版权归我，但 jlox 与 clox 的*代码*与实现使用非常宽松的 [MIT 许可证][mit license]。非常欢迎你[拿去任一解释器][source]，爱怎么用就怎么用。尽情发挥。

    <!--
    If you make significant changes to the language, it would be good to also
    change the name, mostly to avoid confusing people about what the name "Lox"
    represents.
    -->
    若你对语言做了重大改动，最好也改个名字，主要是避免人们混淆 “Lox” 这个名字代表什么。

    </aside>

<!--
    Eventually you may get to a point where you have something you think others
    could use as well. That gets you into the very distinct world of programming
    language *popularity*. Expect to spend a ton of time writing documentation,
    example programs, tools, and useful libraries. The field is crowded with
    languages vying for users. To thrive in that space you'll have to put on
    your marketing hat and *sell*. Not everyone enjoys that kind of
    public-facing work, but if you do, it can be incredibly gratifying to see
    people use your language to express themselves.
-->
    最终你或许会到某一点：手头有了你认为别人也能用的东西。那会把你带进程序设计语言*流行度*那个截然不同的世界。预期要花大量时间写文档、示例程序、工具与有用库。这片领域挤满了争夺用户的语言。要在那里茁壮成长，你得戴上营销帽去*推销*。不是人人都享受那种面向公众的工作；但若你享受，看见人们用你的语言表达自己，会无比满足。

<!--
Or maybe this book has satisfied your craving and you'll stop here. Whichever
way you go, or don't go, there is one lesson I hope to lodge in your heart. Like
I was, you may have initially been intimidated by programming languages. But in
these chapters, you've seen that even really challenging material can be tackled
by us mortals if we get our hands dirty and take it a step at a time. If you can
handle compilers and interpreters, you can do anything you put your mind to.
-->
又或许本书已满足你的渴望，你会停在这里。无论你走哪条路，或不走，有一课我希望嵌进你心里。像我一样，你起初可能被程序设计语言吓到。但在这些章节里，你已看见：即便真正有挑战的材料，只要我们动手、一步一步来，凡人也对付得了。若你能搞定编译器与解释器，你就能做成任何下定决心去做的事。

[mit license]: https://en.wikipedia.org/wiki/MIT_License
[source]: https://github.com/munificent/craftinginterpreters

<div class="challenges">

<!--
-- Challenges
-->
## 挑战

<!--
Assigning homework on the last day of school seems cruel but if you really want
something to do during your summer vacation:
-->
在学期最后一天布置作业显得残忍，但若你暑假真想找点事做：

<!--
1.  Fire up your profiler, run a couple of benchmarks, and look for other
    hotspots in the VM. Do you see anything in the runtime that you can improve?
-->
1.  拉起性能分析器，跑几个基准，在虚拟机里寻找其他热点。运行时里有没有你能改进的地方？

<!--
2.  Many strings in real-world user programs are small, often only a character
    or two. This is less of a concern in clox because we intern strings, but
    most VMs don't. For those that don't, heap allocating a tiny character array
    for each of those little strings and then representing the value as a
    pointer to that array is wasteful. Often, the pointer is larger than the
    string's characters. A classic trick is to have a separate value
    representation for small strings that stores the characters inline in the
    value.

    Starting from clox's original tagged union representation, implement that
    optimization. Write a couple of relevant benchmarks and see if it helps.
-->
2.  真实世界用户程序里的许多字符串很小，常常只有一两个字符。在 clox 里这不太成问题，因为我们驻留字符串，但多数虚拟机不这么做。对那些不驻留的，为每个小字符串堆分配一个小字符数组，再把值表示成指向该数组的指针，很浪费。指针往往比字符串字符还大。经典技巧是为小字符串另设一种值表示，把字符内联存在值里。

    从 clox 原先的带标签联合表示出发，实现该优化。写几个相关基准，看看是否有帮助。

<!--
3.  Reflect back on your experience with this book. What parts of it worked well
    for you? What didn't? Was it easier for you to learn bottom-up or top-down?
    Did the illustrations help or distract? Did the analogies clarify or
    confuse?

    The more you understand your personal learning style, the more effectively
    you can upload knowledge into your head. You can specifically target
    material that teaches you the way you learn best.
-->
3.  回顾你与本书相处的体验。哪些部分对你有效？哪些无效？你更容易自底向上还是自顶向下学习？插图是帮助还是干扰？类比是澄清还是混淆？

    你越了解自己的学习风格，就越能有效地把知识上传进脑子。你可以专门对准以你最擅长的方式教你的材料。

</div>
