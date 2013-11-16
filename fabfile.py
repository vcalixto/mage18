"""
Magento.py

This file will take care of setting your magento project up and deploying it to
your beta and production servers. Please see the README file for information on
how to use this file.

To view how to use any of these tasks, run fab -d COMMAND
"""

from fabric.api import *
from fabric.context_managers import settings
from fabric.contrib.files import contains, exists
from fabric.contrib.project import rsync_project
from os import getcwd

env.forward_agent = True
env.name = None
env.new_relic = False
env.repository = 'git@github.com:vcalixto/mage18.git'
env.user = 'u561770625'
env.group = 'deployer'
env.user_home = '/home/%s' % env.user
env.hosts = []
env.src_path = '%s/public_html' % env.user_home


def production():
    env.name = 'production'
    env.hosts = ['31.170.160.77']
    env.group = 'users'


def staging():
    env.name = 'staging'
    env.hosts = ['31.170.160.79']
    env.group = 'www-data'


def localhost():
    env.name = 'localhost'
    env.hosts = ['127.0.0.1']
    env.src_path = '/var/www/mage18'


def deploy(commit='master'):
    "deploy the code to servers yeah! - USAGE fab environment deploy:tag(1.0.0)"
    if not env.name:
        raise Exception(u'You MUST set the environment variable.')

    # SSH exclude key checking for github.com
    if not exists('%s/.ssh' % env.user_home):
        run('mkdir %s/.ssh' % env.user_home)

    ssh_config = '%s/.ssh/config' % env.user_home
    if not contains(ssh_config, 'Host github.com'):
        run('echo "Host github.com" >>%s' % ssh_config)
        run('echo "     StrictHostKeyChecking no" >>%s' % ssh_config)
        run('echo "     UserKnownHostsFile /dev/null" >>%s' % ssh_config)

    # clone the repo into the env.src_path
    if not exists(env.src_path):
        sudo('mkdir %s' % env.src_path)
        sudo('chown %s:%s %s' % (env.user, env.group, env.src_path))
        run('git clone %s %s' % (env.repository, env.src_path))

    with cd(env.src_path):
        # fetch the changes
        run('git fetch -p')

        #if is a production deploy make sure we're deploying a tag
        if env.name == 'production':
            with settings(warn_only=True):
                if run('git tag | grep \'^%s$\'' % commit).failed:
                    raise RuntimeError(u'In production deploy only tags')

        # checkout to the selected commit/tag/branch
        run('git checkout %s' % commit)

        # if the selected commit is the master branch, merge the changes
        with settings(warn_only=True):
            is_branch = run('git branch -r | grep \'%s\'' % commit).succeeded

            # if the selected commit is the master branch, merge the changes
            if is_branch:
                run('git merge origin/%s' % commit)

    sudo('chown -R %s:%s %s' % (env.user, env.group, env.src_path))
    rsync_project(env.env.src_path,getcwd() + '/',["media","var",".git",".gitignore","app/etc/local.xml","*.py*","sitemap"],True,"-pthrvzL")

def indexer(status=False,mode=False,mode_realtime=False,mode_manual=False,reindex=False):
    """
    Run index.php with your options

    Options:
          status='<indexer>'            Show Indexer(s) Status
          mode='<indexer>'              Show Indexer(s) Index Mode
          mode_realtime='<indexer>'     Set index mode type "Update on Save"
          mode_manual='<indexer>'       Set index mode type "Manual Update"
          reindex='<indexer>'           Reindex Data

    Usage:

        fab production indexer:status='catalog_url'
    """
    if not env.name:
       raise Exception(u'You MUST set the environment variable.')
    
    with cd(env.src_path):
        if status:
            run('php shell/indexer.php --status %s' % status)
        if mode:
            run('php shell/indexer.php --mode %s' % mode)
        if mode_realtime:
            run('php shell/indexer.php --mode-realtime %s' % mode_realtime)
        if mode_manual:
            run('php shell/indexer.php --mode-manual %s' % mode_manual)
        if reindex:
            run('php shell/indexer.php --reindex %s' % reindex)


def indexer_info():
    """
    Show allowed indexers
    """


def indexer_reindexall():
  """
  Reindex Data by all indexers
  """
  if not env.name:
       raise Exception(u'You MUST set the environment variable.')
  with cd(env.src_path):
    run('php shell/indexer.php reindexall')


def log_status():
  """
  Display statistics per log tables
  """
  if not env.name:
       raise Exception(u'You MUST set the environment variable.')
  with cd(env.src_path):
    run('php shell/log.php status')


def log_clean(days=0):
  """
  Clean Logs

  Usage:

      fab production log_clean

  If you want to save the log files, you can pass the number of days to save the
  log files, for example:

      fab production log_clean:7
  """
  if not env.name:
       raise Exception(u'You MUST set the environment variable.')
  with cd(env.src_path):
    if days > 0 and days.isdigit():
        run('php shell/log.php clean --days %s' % days)
    else:
        run('php shell/log.php clean')


def install(version="1.8.0.0",localhost=False):
    """
    Task will install magento

    Eg:

        fab production install:version="1.8.0.0"

    Localhost, run this command:

        fab install:localhost=True
    """
    print 'All questions have defaults, update them if you want to change them'
    install_str = ''
    license_agreement_accepted = prompt('license_agreement_accepted',default='yes')
    install_str += ' --license_agreement_accepted %s' % license_agreement_accepted
    locale = prompt('locale',default='en_US')
    install_str += ' --locale %s' % locale
    timezone = prompt('timezone',default='America/Chicago')
    install_str += ' --timezone %s' % timezone
    default_currency = prompt('default_currency',default='USD')
    install_str += ' --default_currency %s' % default_currency
    db_host = prompt('db_host',default='localhost')
    install_str += ' --db_host %s' % db_host
    db_model = prompt('db_model',default='mysql4')
    install_str += ' --db_model %s' % db_model
    db_name = prompt('db_name',default='magento')
    install_str += ' --db_name %s' % db_name
    db_user = prompt('db_user',default='root')
    install_str += ' --db_user %s' % db_user
    db_pass = prompt('db_pass',default='root')
    install_str += ' --db_pass %s' % db_pass
    db_prefix = prompt('db_prefix')
    if db_prefix:
        install_str += ' --db_prefix %s' % db_prefix
    session_save = prompt('session_save (files|db)',default='files')
    install_str += ' --session_save %s' % session_save
    admin_frontname = prompt('admin_frontname',default='admin')
    install_str += ' --admin_frontname %s' % admin_frontname
    url = '';
    while len(url) <= 0:
        url = prompt('url')
    install_str += ' --url "%s"' % url
    skip_url_validation = prompt('skip_url_validation',default='yes')
    install_str += ' --skip_url_validation %s' % skip_url_validation
    use_rewrites = prompt('use_rewrites',default='yes')
    install_str += ' --use_rewrites %s' % use_rewrites
    use_secure = prompt('use_secure',default='no')
    install_str += ' --use_secure %s' % use_secure
    secure_base_url = prompt('secure_base_url')
    install_str += ' --secure_base_url "%s"' % secure_base_url
    use_secure_admin = prompt('use_secure_admin',default='no')
    install_str += ' --use_secure_admin "%s"' % use_secure_admin
    enable_charts = prompt('enable_charts',default='no')
    install_str += ' --enable_charts %s' % enable_charts
    admin_lastname = prompt('admin_lastname',default='admin')
    install_str += ' --admin_lastname %s' % admin_lastname
    admin_firstname = prompt('admin_firstname',default='admin')
    install_str += ' --admin_firstname %s' % admin_firstname
    admin_email = prompt('admin_email',default='admin@localhost.com')
    install_str += ' --admin_email "%s"' % admin_email
    admin_username = prompt('admin_username',default='admin')
    install_str += ' --admin_username %s' % admin_username
    admin_password = prompt('admin_password',default='magentoadmin123')
    install_str += ' --admin_password "%s"' % admin_password
    encryption_key = prompt('encryption_key')
    if encryption_key:
        install_str += ' --encryption_key "%s"' % encryption_key
    if localhost:
        local('wget http://www.magentocommerce.com/downloads/assets/%s/magento-%s.tar.gz' % (version, version))
        local('tar -zxvf magento-%s.tar.gz' % version)
        local('mv magento/* magento/.htaccess .')
        local('chmod o+w var var/.htaccess app/etc')
        local('chmod -R o+w media')
        local('rm -rf magento/ magento-%s.tar.gz' % version)
        local('rm -rf index.php.sample .htaccess.sample php.ini.sample LICENSE.txt STATUS.txt')
        local('php install.php -- %s' % install_str)
        local('rm install.php')
        if prompt('Would you like to download a .gitignore file?', default=False):
            local('wget --no-check-certificate -O .gitignore https://raw.github.com/github/gitignore/master/Magento.gitignore')
    else:
        run('wget http://www.magentocommerce.com/downloads/assets/%s/magento-%s.tar.gz' % (version, version))
        run('tar -zxvf magento-%s.tar.gz' % version)
        run('mv magento/* magento/.htaccess .')
        run('chmod o+w var var/.htaccess app/etc')
        run('chmod -R o+w media')
        run('rm -rf magento/ magento-%s.tar.gz' % version)
        run('rm -rf index.php.sample .htaccess.sample php.ini.sample LICENSE.txt STATUS.txt')
        run('php install.php -- %s' % install_str)
        run('rm install.php')

