---
hide:
  - navigation
  - toc
---

<div class="landing-page" markdown>

<section class="landing-hero" markdown>

<div class="hero-copy" markdown>

<p class="eyebrow">Local Unix socket client</p>

<h1>Control Herdr <span>from Python.</span></h1>

<p class="lead">A small, typed client for inspecting workspaces, driving panes and listening to events without adding runtime dependencies.</p>

<div class="hero-actions" markdown>

[Get started](getting-started/installation.md){ .md-button .md-button--primary }
[Explore the API](reference/clients.md){ .md-button }

</div>

<div class="install-chip"><code>python -m pip install herdr-client</code></div>

<div class="metric-row">
<span class="metric"><strong>Python</strong> 3.13+</span>
<span class="metric"><strong>Sync</strong> + <strong>Async</strong></span>
<span class="metric"><strong>0</strong> runtime deps</span>
</div>

</div>

<div class="terminal-card" aria-label="Example Herdr client session">
<div class="terminal-bar">
<span class="terminal-dot"></span><span class="terminal-dot"></span><span class="terminal-dot"></span>
<span class="terminal-title">herdr-client / quickstart</span>
</div>
<div class="terminal-body">
<div><span class="terminal-prompt">$</span> <span class="terminal-command">python demo.py</span></div>
<div class="terminal-muted">connecting to ~/.config/herdr/herdr.sock</div>
<div><span class="terminal-success">connected</span> protocol=22</div>
<br>
<div><span class="terminal-muted">workspace</span> main</div>
<div><span class="terminal-muted">pane</span>      build / ready</div>
<div><span class="terminal-muted">output</span>    tests passed</div>
</div>
</div>

</section>

<section class="landing-section" markdown>

<p class="section-kicker">Built for local automation</p>

<h2>Small surface. Useful everywhere.</h2>

<div class="grid cards" markdown>

-   :material-swap-horizontal: **One API, two styles**

    Use blocking methods in scripts or native `asyncio` methods in services. Names,
    parameters and return types stay aligned.

    [:octicons-arrow-right-24: Choose a client](getting-started/concepts.md)

-   :material-shape-outline: **Typed, not restrictive**

    Results are ordinary dictionaries with schema-derived `TypedDict` models, so
    callers keep familiar indexing and iteration.

    [:octicons-arrow-right-24: Explore the types](reference/types.md)

-   :material-lan-connect: **Local by default**

    Connect through an explicit socket, an environment variable or a named Herdr
    session with predictable resolution rules.

    [:octicons-arrow-right-24: Configure the socket](guides/client-configuration.md)

</div>

</section>

<section class="landing-section" markdown>

<p class="section-kicker">Start in seconds</p>

<h2>Pick your style.</h2>

Both clients expose the same operations. Choose a tab and keep that choice across the
rest of the documentation.

=== "Sync"

    ```python
    from herdr_client import HerdrClient

    client = HerdrClient()
    print(client.ping())
    print(client.workspace_list())
    ```

=== "Async"

    ```python
    import asyncio

    from herdr_client import AsyncHerdrClient


    async def main() -> None:
        client = AsyncHerdrClient()
        print(await client.ping())
        print(await client.workspace_list())


    asyncio.run(main())
    ```

</section>

<section class="landing-section" markdown>

<p class="section-kicker">Keep going</p>

<h2>Find the right starting point.</h2>

<div class="grid cards" markdown>

-   :material-rocket-launch-outline: **New to herdr-client?**

    Install the package and make your first request.

    [:octicons-arrow-right-24: Read the quickstart](getting-started/quickstart.md)

-   :material-console-line: **Driving a pane?**

    Send input, read output and wait for a match.

    [:octicons-arrow-right-24: Work with panes](guides/workspaces-and-panes.md)

-   :material-book-open-variant: **Need the details?**

    Browse signatures, models, exceptions and protocol coverage.

    [:octicons-arrow-right-24: Open the reference](reference/clients.md)

</div>

</section>

</div>
