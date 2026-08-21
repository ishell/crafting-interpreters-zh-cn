# 树遍历解释器

<!--
With this part, we begin jlox, the first of our two interpreters. Programming
languages are a huge topic with piles of concepts and terminology to cram into
your brain all at once. Programming language theory requires a level of mental
rigor that you probably haven't had to summon since your last calculus final.
(Fortunately there isn't too much theory in this book.)
-->
从这一部分开始，我们着手打造 jlox——两支解释器中的第一支。程序设计语言是个庞大的话题，成堆的概念与术语会一股脑儿往你脑子里塞。程序语言理论所要求的那种心力投入，大概得追溯到你上一次高等数学期末考了。（幸好，这本书里的理论并不算多。）

<!--
Implementing an interpreter uses a few architectural tricks and design
patterns uncommon in other kinds of applications, so we'll be getting used to
the engineering side of things too. Given all of that, we'll keep the code we
have to write as simple and plain as possible.
-->
实现一支解释器，还会用到一些在其他类型应用里并不常见的架构技巧与设计模式，所以我们也会渐渐熟悉工程实践这一面。话虽如此，我们会尽量把必须亲手写下的代码保持得简单、朴素。

<!--
In less than two thousand lines of clean Java code, we'll build a complete
interpreter for Lox that implements every single feature of the language,
exactly as we've specified. The first few chapters work front-to-back through
the phases of the interpreter -- [scanning][], [parsing][], and
[evaluating code][]. After that, we add language features one at a time,
growing a simple calculator into a full-fledged scripting language.
-->
用不了两千行清爽的 Java 代码，我们就会为 Lox 建起一支完整的解释器，把语言规范里的每一项特性都如实实现出来。开头几章会顺着解释器的各个阶段一路走完——[扫描][scanning]、[语法分析][parsing]，以及[求值][evaluating code]。之后，我们再一次添加一项语言特性，把一台简单的计算器，慢慢长成一门五脏俱全的脚本语言。

[scanning]: scanning.html
[parsing]: parsing-expressions.html
[evaluating code]: evaluating-expressions.html
