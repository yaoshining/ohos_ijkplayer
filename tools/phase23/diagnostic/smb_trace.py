"""Phase23 SMB 协议观测接口。"""
def install(core, commands, emit):
    def register(protocol, number):
        slot = {}
        def handler(connection, server, packet, *args, **kwargs):
            emit('command_begin', protocol=protocol, command=number, connection=connection)
            try:
                result = slot['original'](connection, server, packet, *args, **kwargs)
            except Exception as error:
                emit('command_exception', protocol=protocol, command=number,
                     connection=connection, exception=type(error).__name__)
                raise
            emit('command_end', protocol=protocol, command=number,
                 connection=connection, status=int(result[2]))
            return result
        hook = core.hookSmbCommand if protocol == 'smb1' else core.hookSmb2Command
        slot['original'] = hook(number, handler)
    for protocol, number in commands:
        register(protocol, number)
