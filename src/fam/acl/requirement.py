
CREATE = "create"
UPDATE = "update"
DELETE = "delete"



class BaseRequirement(object):

    action = None

    def __init__(self, user=None, role=(), access=True, owner=False):

        self.user = user
        self.role = role
        self.access = access
        self.owner = owner

    def as_json(self):

        j = {}
        if self.user is not None:
            j["user"] = self.user
        if self.role is not None:
            j["role"] = self.role
        if self.access is False:
            j["withoutAccess"] = True
        if self.owner is True:
            j["owner"] = True

        return j


class CreateRequirement(BaseRequirement):
    pass


class UpdateRequirement(BaseRequirement):

    def __init__(self, user=None, role=(), access=True, owner=False, fields=None):

        super(UpdateRequirement, self).__init__(user=user, role=role, access=access, owner=owner)
        self.fields = fields

    def as_json(self):

        j = super(UpdateRequirement, self).as_json()
        if self.fields is not None:
            j["fields"] = self.fields
        return j


class DeleteRequirement(BaseRequirement):
    pass



