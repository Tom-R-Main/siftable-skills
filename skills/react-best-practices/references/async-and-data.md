# Async And Data

Use this reference for waterfalls, Suspense, API routes, Server Actions, client fetching, event listeners, and browser storage.

## Impact Order

1. Remove request waterfalls before tuning renders. A sequential `await` chain adds full latency at every step.
2. Start independent work early and await late. Use `Promise.all` for independent work and named promises for partial dependencies.
3. Defer async work behind cheap synchronous guards when a branch often exits early.
4. Use Suspense boundaries when only part of a tree needs data and the shell can render first.
5. Deduplicate client fetching and global listeners before adding custom caches.

## Waterfalls

Use `Promise.all` when operations do not depend on each other:

```ts
const [user, posts, settings] = await Promise.all([
  fetchUser(userId),
  fetchPosts(userId),
  fetchSettings(userId),
]);
```

For partial dependencies, start each promise as soon as its inputs exist:

```ts
const userPromise = fetchUser(userId);
const profilePromise = userPromise.then((user) => fetchProfile(user.profileId));
const settingsPromise = fetchSettings(userId);

const [user, profile, settings] = await Promise.all([
  userPromise,
  profilePromise,
  settingsPromise,
]);
```

Prefer this native shape unless the project already uses a dependency scheduler. Do not introduce `better-all` just to satisfy a pattern.

## Cheap Guards

Move expensive async reads behind synchronous guards when the async value is only needed on the guarded path:

```ts
if (!featureEnabledLocally) {
  return fallback;
}

const remoteFlag = await getRemoteFlag("new-dashboard");
return remoteFlag ? next : fallback;
```

Keep the original order when the guard is expensive, depends on the async value, or side effects must happen in sequence.

## API Routes And Server Actions

Start independent operations at the top of the handler. Await authentication before privileged work, but do not make unrelated configuration or lookup calls wait for authentication if they are safe to start.

```ts
export async function GET(request: Request) {
  const sessionPromise = auth();
  const configPromise = loadPublicConfig();

  const session = await sessionPromise;
  const [config, data] = await Promise.all([
    configPromise,
    loadUserData(session.user.id),
  ]);

  return Response.json({ config, data });
}
```

Type the response shape explicitly when it crosses a route or client boundary. Avoid returning broad object literals that widen into optional-everything bags.

## Suspense And Streaming

Use Suspense when a stable shell can render without the slower data. Keep layout-critical or SEO-critical data outside the boundary if streaming would cause layout shift or incomplete first paint.

Pass shared promises to multiple children when they need the same result, or use the framework's request cache. Do not create duplicate fetches in sibling components.

## Client Fetching

Use the project's existing fetching library first. SWR-style deduplication is useful for repeated client requests, but adding SWR is a dependency decision.

Cache keys should be typed and stable. Prefer small serializable tuples or key builders over concatenated strings:

```ts
type UserKey = readonly ["user", string];
const userKey = (userId: string): UserKey => ["user", userId] as const;
```

## Event Listeners

Deduplicate global event listeners. Put one listener at the boundary and fan out through state, context, or a small subscription helper. Mark scroll/touch/wheel listeners as passive when they never call `preventDefault`.

Clean up listeners in effects and keep the handler identity stable without lying to the hook linter. Use `useEffectEvent` where available; otherwise use a ref-backed latest-callback helper already present in the project.

## Storage

Minimize and version `localStorage`/`sessionStorage` data. Storage APIs and cookies are synchronous; cache repeated reads in memory and invalidate on writes, `storage` events, or visibility changes when external updates are possible.

For TypeScript, parse stored data as `unknown`, validate or narrow once, and expose a precise result type downstream.
