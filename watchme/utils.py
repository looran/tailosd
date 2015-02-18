import sys
import os
import pwd
import grp

def droppriv(uid, gid):
    if os.getuid() != 0:
        raise Exception("drop_privileges() called while not root ! (user=%s" % os.getuid())
    # Remove group privileges
    os.setgroups([])
    # Try setting the new uid/gid
    os.setgid(gid)
    os.setuid(uid)
    # Ensure a very conservative umask
    old_umask = os.umask(077)

def init_from_args(obj, just_args=True):
  """ initialise self.* for all caller function local variable.
  if just_args=False, only caller function paramaters are used. """
  caller_name = sys._getframe(1).f_code.co_name
  code_obj = sys._getframe(1).f_code
  for key, value in sys._getframe(1).f_locals.items():
    if ((not just_args)
        or key in code_obj.co_varnames[1:code_obj.co_argcount]):
      setattr(obj, key, value)
