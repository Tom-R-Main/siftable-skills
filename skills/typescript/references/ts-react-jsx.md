# React & JSX typing

Practical patterns for typed React (this repo's frontend: React + Vite, `@/` →
`src` alias). Match existing component idiom first.

## Component props

Type props with a `type` alias; **don't use `React.FC`** (it's fallen out of favor —
it forces an implicit `children`, complicates generics, and adds nothing). Type the
props parameter directly:

```ts
type ButtonProps = {
  label: string;
  onClick: () => void;
  variant?: "primary" | "ghost";   // optional with a literal union
  children?: React.ReactNode;      // declare children explicitly when used
};

function Button({ label, onClick, variant = "primary" }: ButtonProps) {
  return <button className={variant} onClick={onClick}>{label}</button>;
}
```

- `React.ReactNode` — anything renderable (the right type for `children`).
- `React.ReactElement` / `JSX.Element` — a single element specifically.
- Extend DOM props: `type Props = React.ComponentProps<"button"> & { loading?: boolean }`.

## Hooks

```ts
const [count, setCount] = useState(0);              // inferred number
const [user, setUser] = useState<User | null>(null); // annotate when initial is null/empty

const ref = useRef<HTMLInputElement>(null);          // DOM ref (read-only .current)
const timer = useRef<number | undefined>(undefined); // mutable instance value

const [state, dispatch] = useReducer(reducer, initial); // reducer types flow from its signature
```

Annotate `useState` only when the initial value under-specifies the type (e.g.
`null`, `[]`, `{}`). Otherwise let inference work.

## Events

Let the JSX attribute supply the handler type instead of importing event types:

```ts
<input onChange={(e) => setName(e.target.value)} />  // e inferred: ChangeEvent<HTMLInputElement>
```

When typing a standalone handler, name the specific event:
`React.ChangeEvent<HTMLInputElement>`, `React.MouseEvent<HTMLButtonElement>`,
`React.FormEvent<HTMLFormElement>`, `React.KeyboardEvent`.

## Generic components & discriminated props

```ts
type ListProps<T> = { items: T[]; render: (item: T) => React.ReactNode };
function List<T>({ items, render }: ListProps<T>) {
  return <>{items.map(render)}</>;
}
```

Model mutually-exclusive prop combinations as a **discriminated union of props** so
illegal combinations don't typecheck:

```ts
type AlertProps =
  | { variant: "error"; error: Error }
  | { variant: "info"; message: string };
```

## Gotchas

- **`.tsx`, not `.ts`**, for any file containing JSX. In `.ts`, `<T>` is parsed as
  a cast and breaks; use `<T,>` for a type param in a `.tsx` arrow function if it's
  ambiguous.
- `useState<T>()` with no initial value infers `T | undefined` — pass an initial or
  annotate.
- Event handlers passed to children: type them at the prop boundary, not inline.
- Prefer `satisfies` over `as` when shaping a styles/config object so you keep
  literal inference *and* get checking (see `ts-config-modules.md` / SKILL Gotchas).
