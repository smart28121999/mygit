class Product:
    def __init__(self,id,name,price):
        self.id=id
        self.name=name
        self.price=price
        
class Shopping:
    def __init__(self):
        self.items=[]
        
    def add_product(self, id, name, price):
        new_prod=Product(id,name,price)
        self.items.append(new_prod)
        print('Product added succesfully!! :)')
        
    def display_prods(self):
        print('Your Products : ')
        for prod in self.items:
            print(f"ID: {prod.id}, Name: {prod.name}, Price: {prod.price}")
            
    def delete_prod(self,id):
        for prod in self.items:
            if prod.id==id:
                self.items.remove(prod)
                print("Product Removed")
    
def main():
        shop = Shopping()
        
        while True:
            print('1.Add Product')
            print('2.View Products')
            print('3.Delete Product')
            print('4.Exit')
            
            choice = int(input('Enter Your Choice'))
            
            match choice:
                case 1: 
                    id=int(input('Enter ID: '))
                    Name=input('ENter Name: ')
                    Price=input('Enter Price: ')
                    shop.add_product(id,Name,Price)
                    
                case 2:
                    shop.display_prods()
                
                case 3:
                    id=int(input('Enter ID: '))
                    shop.delete_prod(id)
                    
                case 4:
                    print('Thank you for shopping')
                    break
                
                case _:
                    print('INvalid Choice')
                    
if __name__ == "__main__":
    main()