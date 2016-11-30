from cloudant.query import Query


class CloudantRecipeStore(object):
    def __init__(self, client, db_name):
        self.client = client
        self.db_name = db_name

    def init(self):
        try:
            self.client.connect()
            print 'Getting database...'
            if self.db_name not in self.client.all_dbs():
                print 'Creating database {}...'.format(self.db_name)
                self.client.create_database(self.db_name)
            else:
                print 'Database {} exists.'.format(self.db_name)
        finally:
            self.client.disconnect()

    # User

    def add_user(self, user_id):
        user_doc = {
            'type': 'user',
            'name': user_id
        }
        return self.add_doc_if_not_exists(user_doc, 'name')

    # Ingredients

    @staticmethod
    def get_unique_ingredients_name(ingredient_str):
        ingredients = [x.strip() for x in ingredient_str.lower().strip().split(',')]
        ingredients.sort()
        return ','.join([x for x in ingredients])

    def find_ingredient(self, ingredient_str):
        return self.find_doc('ingredient', 'name', self.get_unique_ingredients_name(ingredient_str))

    def add_ingredient(self, ingredient_str, matching_recipes, user_doc):
        ingredient_doc = {
            'type': 'ingredient',
            'name': self.get_unique_ingredients_name(ingredient_str),
            'recipes': matching_recipes
        }
        ingredient_doc = self.add_doc_if_not_exists(ingredient_doc, 'name')
        self.increment_ingredient_for_user(ingredient_doc, user_doc)
        return ingredient_doc

    def increment_ingredient_for_user(self, ingredient_doc, user_doc):
        try:
            self.client.connect()
            # get latest user
            latest_user_doc = self.client[self.db_name][user_doc['_id']]
            # see if user has an array of ingredients, if not create it
            if 'ingredients' not in latest_user_doc.keys():
                latest_user_doc['ingredients'] = []
            # find the ingredient that matches the name of the passed in ingredient
            # if it doesn't exist create it
            user_ingredient = None
            for ingredient in latest_user_doc['ingredients']:
                if ingredient['name'] == ingredient_doc['name']:
                    user_ingredient = ingredient
                    break
            if user_ingredient is None:
                user_ingredient = {'name': ingredient_doc['name']}
                latest_user_doc['ingredients'].append(user_ingredient)
            # see if the user_ingredient exists, if not create it
            if 'count' not in user_ingredient.keys():
                user_ingredient['count'] = 0
            # increment the count on the user_ingredient
            user_ingredient['count'] += 1
            # save the user doc
            latest_user_doc.save()
        finally:
            self.client.disconnect()

    # Cuisine

    @staticmethod
    def get_unique_cuisine_name(cuisine):
        return cuisine.strip().lower()

    def find_cuisine(self, cuisine_str):
        return self.find_doc('cuisine', 'name', self.get_unique_cuisine_name(cuisine_str))

    def add_cuisine(self, cuisine_str, matching_recipes, user_doc):
        cuisine_doc = {
            'type': 'cuisine',
            'name': self.get_unique_cuisine_name(cuisine_str),
            'recipes': matching_recipes
        }
        cuisine_doc = self.add_doc_if_not_exists(cuisine_doc, 'name')
        self.increment_cuisine_for_user(cuisine_doc, user_doc)
        return cuisine_doc

    def increment_cuisine_for_user(self, cuisine_doc, user_doc):
        try:
            self.client.connect()
            # get latest user
            latest_user_doc = self.client[self.db_name][user_doc['_id']]
            # see if user has an array of cuisines, if not create it
            if 'cuisines' not in latest_user_doc.keys():
                latest_user_doc['cuisines'] = []
            # find the cuisine that matches the name of the passed in cuisine
            # if it doesn't exist create it
            user_cuisine = None
            for cuisine in latest_user_doc['cuisines']:
                if cuisine['name'] == cuisine_doc['name']:
                    user_cuisine = cuisine
                    break
            if user_cuisine is None:
                user_cuisine = {'name': cuisine_doc['name']}
                latest_user_doc['cuisines'].append(user_cuisine)
            # see if the user_cuisine exists, if not create it
            if 'count' not in user_cuisine.keys():
                user_cuisine['count'] = 0
            # increment the count on the user_cuisine
            user_cuisine['count'] += 1
            # save the user doc
            latest_user_doc.save()
        finally:
            self.client.disconnect()

    # Recipe

    @staticmethod
    def get_unique_recipe_name(recipe_id):
        return str(recipe_id).strip().lower()

    def find_recipe(self, recipe_id):
        return self.find_doc('recipe', 'name', self.get_unique_recipe_name(recipe_id))

    def find_favorite_recipes_for_user(self, user_doc, count):
        try:
            self.client.connect()
            db = self.client[self.db_name]
            latest_user_doc = db[user_doc['_id']]
            if 'recipes' in latest_user_doc.keys():
                user_recipes = latest_user_doc['recipes']
                user_recipes.sort(key=lambda x: x['count'], reverse=True)
                recipes = []
                for i, recipe in enumerate(user_recipes):
                    if i >= count:
                        break
                    recipes.append(recipe)
                return recipes
            else:
                return []
        finally:
            self.client.disconnect()

    def add_recipe(self, recipe_id, recipe_title, recipe_detail, ingredient_cuisine_doc, user_doc):
        recipe = {
            'type': 'recipe',
            'name': self.get_unique_recipe_name(recipe_id),
            'title': recipe_title.strip(),
            'instructions': recipe_detail
        }
        recipe = self.add_doc_if_not_exists(recipe, 'name')
        self.increment_recipe_for_user(recipe, ingredient_cuisine_doc, user_doc)
        return recipe

    def increment_recipe_for_user(self, recipe_doc, ingredient_cuisine_doc, user_doc):
        try:
            self.client.connect()
            # get latest user
            latest_user_doc = self.client[self.db_name][user_doc['_id']]
            # see if user has an array of recipes, if not create it
            if 'recipes' not in latest_user_doc.keys():
                latest_user_doc['recipes'] = []
            # find the recipe that matches the name of the passed in recipe
            # if it doesn't exist create it
            user_recipe = None
            for recipe in latest_user_doc['recipes']:
                if recipe['id'] == recipe_doc['name']:
                    user_recipe = recipe
                    break
            if user_recipe is None:
                user_recipe = {
                    'id': recipe_doc['name'],
                    'title': recipe_doc['title']
                }
                latest_user_doc['recipes'].append(user_recipe)
            # see if the user_recipe exists, if not create it
            if 'count' not in user_recipe.keys():
                user_recipe['count'] = 0
            # increment the count on the user_recipe
            user_recipe['count'] += 1
            # save the user doc
            latest_user_doc.save()
        finally:
            self.client.disconnect()

    # Cloudant Helper Methods

    def find_doc(self, doc_type, property_name, property_value):
        try:
            self.client.connect()
            db = self.client[self.db_name]
            selector = {
                '_id': {'$gt': 0},
                'type': doc_type,
                property_name: property_value
            }
            query = Query(db, selector=selector)
            for doc in query()['docs']:
                return doc
            return None
        finally:
            self.client.disconnect()

    def add_doc_if_not_exists(self, doc, unique_property_name):
        doc_type = doc['type']
        property_value = doc[unique_property_name]
        existing_doc = self.find_doc(doc_type, unique_property_name, property_value)
        if existing_doc is not None:
            print 'Returning {} doc where {}={}'.format(doc_type, unique_property_name, property_value)
            return existing_doc
        else:
            print 'Creating {} doc where {}={}'.format(doc_type, unique_property_name, property_value)
            try:
                self.client.connect()
                db = self.client[self.db_name]
                return db.create_document(doc)
            finally:
                self.client.disconnect()
