-- ieee.lua -- give the pandoc AST an IEEE-conference look:
--   * level-1 sections numbered with Roman numerals ("I.", "II.", ...), References left unnumbered
--   * level-2 subsections numbered with letters ("A.", "B.", ...), reset within each section
--   * level-4 run-in headings ("\paragraph") left untouched
--   * tables labelled "Table I", "Table II", ... (the reference.docx small-caps caption
--     style renders these as "TABLE I")
-- The small-caps rendering of the labels is done by the Word styles in paper/reference.docx.

local function roman(n)
  local vals = {1000,900,500,400,100,90,50,40,10,9,5,4,1}
  local syms = {"M","CM","D","CD","C","XC","L","XL","X","IX","V","IV","I"}
  local out = ""
  for i = 1, #vals do
    while n >= vals[i] do out = out .. syms[i]; n = n - vals[i] end
  end
  return out
end

local sec = 0   -- level-1 section counter
local sub = 0   -- level-2 subsection counter (reset each section)
local tbl = 0   -- table counter

function Header(el)
  if el.level == 1 then
    if pandoc.utils.stringify(el) == "References" then
      return el                       -- bibliography heading stays unnumbered
    end
    sec = sec + 1
    sub = 0
    table.insert(el.content, 1, pandoc.Space())
    table.insert(el.content, 1, pandoc.Str(roman(sec) .. "."))
    return el
  elseif el.level == 2 then
    sub = sub + 1
    local letter = string.char(string.byte("A") + sub - 1)
    table.insert(el.content, 1, pandoc.Space())
    table.insert(el.content, 1, pandoc.Str(letter .. "."))
    return el
  end
  return el
end

-- ---------------------------------------------------------------------------
-- Convert inline/display math to plain Unicode text. pandoc otherwise emits Word
-- equation objects (OMML) for every $...$, which Quick Look, Pages, and Google Docs
-- render poorly (numbers vanish, cells look empty). As plain Unicode the content
-- renders identically in every viewer.
local GREEK = {rho="\u{03C1}", tau="\u{03C4}", alpha="\u{03B1}", beta="\u{03B2}",
  gamma="\u{03B3}", delta="\u{03B4}", Delta="\u{0394}", epsilon="\u{03B5}",
  mu="\u{03BC}", sigma="\u{03C3}", Sigma="\u{03A3}", lambda="\u{03BB}",
  chi="\u{03C7}", pi="\u{03C0}", theta="\u{03B8}", phi="\u{03C6}"}
local SYM = {approx="\u{2248}", neq="\u{2260}", leq="\u{2264}", geq="\u{2265}",
  le="\u{2264}", ge="\u{2265}", sim="\u{223C}", times="\u{00D7}", pm="\u{00B1}",
  cdot="\u{00B7}", ["in"]="\u{2208}", notin="\u{2209}", rightarrow="\u{2192}",
  leftarrow="\u{2190}", leftrightarrow="\u{2194}", to="\u{2192}", ll="\u{226A}",
  gg="\u{226B}", equiv="\u{2261}", propto="\u{221D}", mid="|", ldots="\u{2026}",
  dots="\u{2026}", infty="\u{221E}", star="*", ast="*", circ="\u{2218}"}
local SUP = {["0"]="\u{2070}",["1"]="\u{00B9}",["2"]="\u{00B2}",["3"]="\u{00B3}",
  ["4"]="\u{2074}",["5"]="\u{2075}",["6"]="\u{2076}",["7"]="\u{2077}",["8"]="\u{2078}",
  ["9"]="\u{2079}",["+"]="\u{207A}",["-"]="\u{207B}",["="]="\u{207C}",["("]="\u{207D}",
  [")"]="\u{207E}",["n"]="\u{207F}",["i"]="\u{2071}"}
local SUB = {["0"]="\u{2080}",["1"]="\u{2081}",["2"]="\u{2082}",["3"]="\u{2083}",
  ["4"]="\u{2084}",["5"]="\u{2085}",["6"]="\u{2086}",["7"]="\u{2087}",["8"]="\u{2088}",
  ["9"]="\u{2089}",["+"]="\u{208A}",["-"]="\u{208B}",["="]="\u{208C}",["("]="\u{208D}",
  [")"]="\u{208E}"}

local function to_script(s, map)
  return (s:gsub(".", function(c) return map[c] or c end))
end

local function demath(s)
  s = s:gsub("\\[,!:;>]", " "):gsub("\\ ", " ")   -- thin-space macros
  s = s:gsub("\\%%", "%%")                          -- \% -> %
  for _ = 1, 4 do s = s:gsub("\\%a+%s*{(.-)}", "%1") end  -- \mathbf{x}, \text{x}, ... -> x
  s = s:gsub("\\(%a+)", function(c) return GREEK[c] or SYM[c] or c end)
  s = s:gsub("%^{(.-)}", function(x) return to_script(x, SUP) end)
  s = s:gsub("_{(.-)}", function(x) return to_script(x, SUB) end)
  s = s:gsub("%^(%w)", function(x) return to_script(x, SUP) end)
  s = s:gsub("_(%w)", function(x) return to_script(x, SUB) end)
  s = s:gsub("[{}$]", ""):gsub("%s+", " ")
  return (s:gsub("^%s+", ""):gsub("%s+$", ""))
end

function Math(el)
  return pandoc.Str(demath(el.text))
end

function Table(el)
  tbl = tbl + 1
  local label = pandoc.Str("Table " .. roman(tbl) .. ".")
  local cap = el.caption
  if cap and cap.long and #cap.long > 0 and cap.long[1].content then
    table.insert(cap.long[1].content, 1, pandoc.Space())
    table.insert(cap.long[1].content, 1, label)
  else
    el.caption.long = {pandoc.Plain({label})}
  end
  return el
end
