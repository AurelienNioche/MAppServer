from django.core.management.base import BaseCommand
from django_celery_beat.models import IntervalSchedule, PeriodicTask
# from background_task.models import Task


class Command(BaseCommand):
    help = 'Register tasks'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):

        # for poll_id in options['poll_ids']:
        #     try:
        #         poll = Poll.objects.get(pk=poll_id)
        #     except Poll.DoesNotExist:
        #         raise CommandError('Poll "%s" does not exist' % poll_id)
        #
        #     poll.opened = False
        #     poll.save()

        every_2_seconds, _ = IntervalSchedule.objects.get_or_create(
            every=2, period=IntervalSchedule.SECONDS,
        )
        PeriodicTask.objects.update_or_create(
            task="assistant.tasks.update_beliefs",
            name="update beliefs",
            defaults=dict(
                interval=every_2_seconds,
                expire_seconds=1,  # If not run within 60 seconds, forget it; another one will be scheduled soon.
            ),
        )
        # revise_beliefs.schedule(repeat=10) #, time=datetime.now()), #time=datetime.time(hour=8, minute=0))
        # revise_beliefs()

        self.stdout.write(self.style.SUCCESS('Successfully registered the tasks'))
