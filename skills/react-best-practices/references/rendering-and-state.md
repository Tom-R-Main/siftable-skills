# Rendering And State

Use this reference for rerenders, memoization, hook dependencies, derived state, transitions, hydration, JSX shape, and rendering behavior.

## Rerender Priority

1. Remove unnecessary state and effects.
2. Reduce subscriptions and props that change too often.
3. Split expensive components or hooks along real dependency boundaries.
4. Memoize only when it removes meaningful work or stabilizes a hot child boundary.
5. Use transitions/deferred values for responsiveness when expensive renders are still necessary.

## Derived State

Derive values during render when they can be computed from current props/state. Do not use an effect just to set another piece of state from existing state.

```tsx
function UserBadge({ user }: { user: User }) {
  const isAdmin = user.role === "admin";
  return <Badge tone={isAdmin ? "danger" : "neutral"}>{user.name}</Badge>;
}
```

Use state for values that change independently over time, not for values that can be recomputed.

## Effects

Move interaction-specific logic into event handlers. Effects are for synchronizing with external systems, not for responding to every internal state transition.

Use primitive dependencies where possible. Instead of depending on a full object, extract the precise values used by the effect. Do not silence the hook linter with `as`, disable comments, or intentionally incomplete dependency arrays.

## Memoization

Do not wrap simple primitive expressions in `useMemo`. The memo bookkeeping can cost more than the expression.

Memoize expensive calculations, expensive child subtrees, or props passed to memoized children. Hoist default non-primitive values to module scope so memoized components do not receive a new array/object/function every render.

Do not define components inside components. The nested component type changes on every render, which forces remounts and loses state.

## State Updates

Use functional `setState` when the next value depends on the previous value. This keeps callbacks stable and avoids stale closures.

Use lazy state initialization for expensive initial values:

```tsx
const [index] = useState(() => buildSearchIndex(items));
```

Use refs for transient values that change frequently but should not trigger renders, such as animation frame IDs, pointer positions, and latest callback references.

## Transitions And Deferred Values

Use `startTransition` for non-urgent state updates that can lag behind direct input. Use `useDeferredValue` when an expensive derived render should trail a fast-changing value.

Do not transition updates that must be immediately visible for accessibility, input correctness, or form validation feedback.

## Hydration

Prefer server-stable output. When a value truly differs between server and client, choose the smallest tool:

- Inline bootstrap data or scripts for client-only values that must avoid flicker.
- `suppressHydrationWarning` only for known, isolated mismatches such as timestamps.
- Client-only rendering only when server output would be misleading or impossible.

Do not hide broad hydration errors. Fix invalid HTML, nondeterministic render logic, random IDs, locale/timezone drift, and unguarded browser APIs.

## Rendering Details

Use explicit ternaries for conditional rendering when the left side can be `0`, `""`, or another renderable value. `condition && <Thing />` is fine only when `condition` is definitely boolean.

Hoist static JSX outside components when it is large and truly static. Use `content-visibility` for long offscreen lists where browser support and layout constraints are acceptable.

Animate wrappers around complex SVGs instead of mutating expensive SVG internals when possible. Reduce SVG coordinate precision when assets are overly large and visual fidelity is unchanged.
