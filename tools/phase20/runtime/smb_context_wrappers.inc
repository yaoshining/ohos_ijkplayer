/* Included by the real Samba context source and the controlled host harness.
 * The harness verifies coordination, not Samba parsing/network behaviour. */
SMBCCTX *smbc_new_context(void)
{
    SMBCCTX *c;
    if (rt_lock()) return NULL;
    if (rt_begin()) { rt_unlock(); return NULL; }
    c = smbc_new_context_runtime_original();
    if (c) rt_add_context();
    int saved = errno; rt_unlock(); errno = saved;
    return c;
}
SMBCCTX *smbc_init_context(SMBCCTX *c)
{
    SMBCCTX *result;
    if (rt_lock()) return NULL;
    if (rt_begin()) { rt_unlock(); return NULL; }
    result = smbc_init_context_runtime_original(c);
    int saved = errno; rt_unlock(); errno = saved;
    return result;
}
int smbc_free_context(SMBCCTX *c, int shutdown)
{
    int result;
    if (rt_lock()) return 1;
    result = smbc_free_context_runtime_original(c, shutdown);
    int saved = errno;
    if (!result && rt_remove_context()) SMBC_module_terminate();
    rt_unlock(); errno = saved;
    return result;
}
