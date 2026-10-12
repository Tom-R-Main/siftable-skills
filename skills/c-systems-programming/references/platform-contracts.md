# Official platform contracts

This source map accompanies the repository's original MIT workflow. It contains
links, not copied tutorial text or examples. Consult the deployed platform's
versioned interfaces; Linux behavior is not automatically a POSIX guarantee.

- [POSIX.1-2024](https://pubs.opengroup.org/onlinepubs/9799919799/): portable
  interface definitions, process and thread behavior, and feature requirements.
- [Linux man-pages](https://www.kernel.org/doc/man-pages/): Linux kernel and libc
  reference project.
- [read(2)](https://man7.org/linux/man-pages/man2/read.2.html) and
  [write(2)](https://man7.org/linux/man-pages/man2/write.2.html): progress and
  error contracts.
- [close(2)](https://man7.org/linux/man-pages/man2/close.2.html): resource release
  and platform-sensitive failure handling.
- [fork(2)](https://man7.org/linux/man-pages/man2/fork.2.html),
  [posix_spawn(3)](https://man7.org/linux/man-pages/man3/posix_spawn.3.html), and
  [waitpid(2)](https://man7.org/linux/man-pages/man2/waitpid.2.html): launch and
  child-lifetime contracts.
- [signal-safety(7)](https://man7.org/linux/man-pages/man7/signal-safety.7.html),
  [sigaction(2)](https://man7.org/linux/man-pages/man2/sigaction.2.html), and
  [pipe(7)](https://man7.org/linux/man-pages/man7/pipe.7.html): handler safety,
  notification, and pipe semantics.

The POSIX site may restrict automated retrieval. An inaccessible page is not
verified source content; use locally available documentation or report the
limitation when a disputed portable guarantee depends on it.
