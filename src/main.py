from pattern import Pattern
from view import View
from presenter import Presenter

view = View()
presenter = Presenter(view)

presenter.start()
view.start()
