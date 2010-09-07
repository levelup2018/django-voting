from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.db import models

from voting.managers import VoteManager

SCORES = (
    (u'+1', +1),
    (u'-1', -1),
)
COUNT_ATTRIBUTES = {}
SCORE_ATTRIBUTES = {}

def cls_module_name(cls):
    return cls.__module__.split('.')[-2]+'.'+cls.__name__.lower()

class VotingCountField(models.IntegerField):
    def __init__(self,*args,**kwargs):
        kwargs['default'] = 0
        super(VotingCountField,self).__init__(*args,**kwargs)

    def contribute_to_class(self,cls,name):
        super(VotingCountField,self).contribute_to_class(cls,name)
        COUNT_ATTRIBUTES[cls_module_name(cls)] = name

class VotingScoreField(models.IntegerField):
    def __init__(self,*args,**kwargs):
        kwargs['default'] = 0
        super(VotingScoreField,self).__init__(*args,**kwargs)

    def contribute_to_class(self,cls,name):
        super(VotingScoreField,self).contribute_to_class(cls,name)
        SCORE_ATTRIBUTES[cls_module_name(cls)] = name

class Vote(models.Model):
    """
    A vote on an object by a User.
    """
    user         = models.ForeignKey(User)
    content_type = models.ForeignKey(ContentType)
    object_id    = models.PositiveIntegerField()
    object       = generic.GenericForeignKey('content_type', 'object_id')
    vote         = models.SmallIntegerField(choices=SCORES)

    objects = VoteManager()

    def save(self,*args,**kwargs):
        super(Vote,self).save(*args,**kwargs)
        content_type = self.content_type
        cls_name = content_type.app_label + '.' + content_type.model
        if not ( cls_name in COUNT_ATTRIBUTES or cls_name in SCORE_ATTRIBUTES ):
            return
        obj = self.object
        score = Vote.objects.get_score(obj)

        if cls_name in COUNT_ATTRIBUTES:
            setattr(obj,COUNT_ATTRIBUTES[cls_name],score['num_votes'])
        if cls_name in SCORE_ATTRIBUTES:
            setattr(obj,SCORE_ATTRIBUTES[cls_name],score['score'])
        obj.save()


    class Meta:
        db_table = 'votes'
        # One vote per user per object
        unique_together = (('user', 'content_type', 'object_id'),)

    def __unicode__(self):
        return u'%s: %s on %s' % (self.user, self.vote, self.object)

    def is_upvote(self):
        return self.vote == 1

    def is_downvote(self):
        return self.vote == -1
