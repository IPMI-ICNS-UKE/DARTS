%---
%layout: default
%title: Usage Information Jekyll Theme
%nav_order: 8
%---

# **How to use Jekyll Theme**


Here is a quick guideline and lookup table on how to use a Jekyll theme for our github page.
**Just the Docs** is our chosen theme. For more information, please visit [Just the Docs](https://just-the-docs.github.io/just-the-docs/).

---
## Typography

### Font size 
{: .text-purple-000}
In Markdown, use the `{: }` wrapper to apply custom classes:

```markdown
Font size 4
{: .fs-4 }
Font size 5
{: .fs-5 }
Font size 6
{: .fs-6 }
```

> Font size 4
> {: .fs-4 }
> Font size 5
> {: .fs-5 }
> Font size 6
> {: .fs-6 }


### Font weight
{: .text-purple-000}

```markdown
Font weight 300
{: .fw-300 }
Font weight 400
{: .fw-400 }
Font weight 500
{: .fw-500 }
Font weight 700
{: .fw-700 }
```

> Font weight 300
> {: .fw-300 }
> Font weight 400
> {: .fw-400 }
> Font weight 500
> {: .fw-500 }
> Font weight 700
> {: .fw-700 }


### Headings
{: .text-purple-000}

```markdown
**Bold**
```

> **Bold**


```markdown
***Bold & italic***
```

> ***Bold & italic***


```markdown
_italic_
```

> _italic_

```markdown
~~strikethrough~~.
```

> ~~strikethrough~~.


### Text color
{: .text-purple-000}

You can find a list of text colors [here](https://just-the-docs.github.io/just-the-docs/docs/utilities/color/).

```markdown
Purple Text
{: .text-purple-000}

Red Text
{: .text-red-300}
```

> Purple Text
> {: .text-purple-000}

> Red Text
> {: .text-red-300}

---

## Links

### General links
{: .text-purple-000}

To include links in your text, type:

```markdown
[link](http://example.com/)
```

> [link](http://example.com/)

### Link to a github page
{: .text-purple-000}

```markdown
[Postprocessing Components]({% link Postprocessing/Postprocessing Components.md %}#Postprocessing Components)
```

> [Postprocessing Components]({% link Postprocessing/Postprocessing Components.md %}#Postprocessing Components)

Another useful example:

> [link to our github issue page](https://github.com/IPMI-ICNS-UKE/T-DARTS/issues).

### Buttons
{: .text-purple-000}

```markdown
[View it on GitHub](https://github.com/IPMI-ICNS-UKE/T-DARTS){: .btn .btn-purple }
```
[View it on GitHub](https://github.com/IPMI-ICNS-UKE/T-DARTS){: .btn .btn-purple }

You can also set the size and color of the button. Here are some examples

```markdown
[View it on GitHub](https://github.com/IPMI-ICNS-UKE/T-DARTS){: .btn .fs-5 .mb-4 .mb-md-0 }
[Link button](http://example.com/){: .btn .btn-green }
[Link button](http://example.com/){: .btn .btn-outline }
```

[View it on GitHub](https://github.com/IPMI-ICNS-UKE/T-DARTS){: .btn .fs-5 .mb-4 .mb-md-0 }

[Link button](http://example.com/){: .btn .btn-green }

[Link button](http://example.com/){: .btn .btn-outline }


---

## Lists

### Bulletpoints
{: .text-purple-000}

```markdown
- Bullet point 1
- Bullet point 2
```

> - Bullet point 1
> - Bullet point 2

### Ordered List
{: .text-purple-000}

```markdown
1. Item 1
1. Item 2
1. Item 3
```

> 1. Item 1
> 1. Item 2
> 1. Item 3


### Task list
{: .text-purple-000}

```markdown
- [ ] todo item
- [ ] todo item
- [x] done
```

> - [ ] todo item
> - [ ] todo item
> - [x] done

---

## Code snippets
First write **```yaml**

then in the next line your code 
and end in the following line with

**```**

The output looks like this:

```yaml
# Kommentare
parameter: "xzy"
```

---
## Inline Code


```markdown
Text text text text, `<inline code snippet>` text text text text text text text text text text text text text text text text text text text text.
## Heading with `<inline code snippet>` in it.
```

---

## Callouts

### Note
{: .text-purple-000}

```markdown
{: .note-title }
> Note
>
> A paragraph with a custom title callout
```

{: .note-title }
> Note
>
> A paragraph with a custom title callout

### Highlight
{: .text-purple-000}

```markdown
{: .highlight }
> Text you want to highlight
> 
> A paragraph
```

{: .highlight }
> Text you want to highlight
> 
> A paragraph

### Important
{: .text-purple-000}

```markdown
{: .important }
> something important 
> 
> A paragraph
```

{: .important }
> something important 
> 
> A paragraph

### Warning
{: .text-purple-000}

```markdown
{: .warning } 
Any warning message
```

{: .warning } 
Any warning message

### New
{: .text-purple-000}

```markdown
{: .new }
Any new things
```

{: .new }
Any new things


**Further examples:**

### Indented multi-paragraph callouts:
{: .text-purple-000}

```markdown
> {: .new }
> > A paragraph
> >
> > Another paragraph
> >
> > The last paragraph
```

> {: .new }
> > A paragraph
> >
> > Another paragraph
> >
> > The last paragraph

```markdown
{: .note-title }
> My note title
>
> A paragraph with a custom title callout
> 
```

{: .note-title }
> My note title
>
> A paragraph with a custom title callout
> 

You can also highlight text as follows: 

```markdown
`hightlighted text`
```

> `hightlighted text`

---


## Table

```markdown

| column 1 | column 2           | column 3 |
|:---------|:-------------------|:---------|
| 1        | something          | helo     |
| 2        | something          | helo     |
| 3        | good `highlight`   | helo     |
| 4        | good `highlight`   | helo     |
```

| column 1 | column 2           | column 3 |
|:---------|:-------------------|:---------|
| 1        | something          | helo     |
| 2        | something          | helo     |
| 3        | good `highlight`   | helo     |
| 4        | good `highlight`   | helo     |


## Labels

Use labels as a way to add an additional mark to a section of your docs. Labels come in a few colors. 
By default, labels will be blue.

```markdown
Default label
{: .label }

Blue label
{: .label .label-blue }

Stable
{: .label .label-green }

New release
{: .label .label-purple }

Coming soon
{: .label .label-yellow }

Deprecated
{: .label .label-red }
```

Default label
{: .label }

Blue label
{: .label .label-blue }

Stable
{: .label .label-green }

New release
{: .label .label-purple }

Coming soon
{: .label .label-yellow }

Deprecated
{: .label .label-red }

---

## Insert image

```markdown
![image tooltip here](/assets/img/Logo.PNG)
```

![image tooltip here](/assets/img/Logo.PNG)
