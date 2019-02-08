import React, { Component } from 'react';
import {Link} from 'react-router-dom';

class Navbar extends Component {
	constructor(props) {
		super(props)
	}
	render() {
		const {loggedIn} = this.props
		if (loggedIn) {
			const loginButton = <Link to="/login">Log in</Link>;
		} else {
			const loginButton = <Link to="/logout">Log Out</Link>;
		}
		return (
			<div className="col-sm-2">
			  <nav className="Navbar">
				<ul class="sidebar-nav">
				  <li><Link to="/">Home</Link></li>
				  <li>Restaurants</li>
				  <li>Reservations</li>
				  <li>{loginButton}</li>
				  <li></li>
				</ul>
			  </nav>
			</div>
		);
	}
}

export default Navbar;
