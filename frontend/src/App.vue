<template>
  <div class="app-shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">Catalonia Legal Engine</p>
        <h1>Arras Contract System</h1>
      </div>
      <nav>
        <RouterLink to="/">Dashboard</RouterLink>
      </nav>
    </header>
    <main>
      <RouterView />
    </main>
  </div>
</template>
