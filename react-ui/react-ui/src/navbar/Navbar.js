import React, { Component } from 'react';

class Navbar extends Component {
	constructor(props) {
		super(props)
	}
	render() {
		return (
			<div className="col-sm-2">
			  <nav className="Navbar">
				<ul class="sidebar-nav">
				  <li>Home</li>
				  <li>Restaurants</li>
				  <li>Reservations</li>
				  <li>Log out</li>
				  <li>Log in</li>
				</ul>
			  </nav>
			</div>
		);
	}
}

export default Navbar;
