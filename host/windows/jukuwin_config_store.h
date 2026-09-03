#ifndef JUKUWIN_CONFIG_STORE_H
#define JUKUWIN_CONFIG_STORE_H

int jh_jukuwin_config_replace(const char *temporary, const char *target,
                              const char *backup,
                              unsigned long *windows_error);

#endif
